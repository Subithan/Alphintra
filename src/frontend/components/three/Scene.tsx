"use client";

import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import * as THREE from "three";
import { useFrame, useLoader, useThree } from "@react-three/fiber";
import gsap from "gsap";

const DEPTH_NEAR = -1.1;
const DEPTH_SPAN = 44;
const DEPTH_FAR = DEPTH_NEAR - DEPTH_SPAN;
const MAX_SPRITES = 360;
const REPULSE_COOLDOWN = 0.12;
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));
const COLLISION_FRAME_STEP = 3; // run overlap resolution every 3 frames to trim CPU spikes
const START_PROGRESS_WINDOW = 0.18;
const END_PROGRESS_WINDOW = 0.84;

export default function Scene() {
  return (
    <>
      <color attach="background" args={["#000000"]} />
      <CoinField />
    </>
  );
}

type Item = {
  base: THREE.Vector3;
  ampX: number;
  ampY: number;
  speedX: number;
  speedY: number;
  phaseX: number;
  phaseY: number;
  driftX: number;
  driftY: number;
  rot: number;
  scale: number;
  depth: number;
  twinkle: number;
  orbitRadius: number;
  orbitPhase: number;
  orbitTilt: number;
  orbitSpeed: number;
};

type ScrollSnapshot = {
  rawProgress: number;
  progress: number;
  easedProgress: number;
  velocity: number;
  depthOffset: number;
};

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(media.matches);
    update();
    if (typeof media.addEventListener === "function") {
      media.addEventListener("change", update);
      return () => media.removeEventListener("change", update);
    }
    media.addListener(update);
    return () => media.removeListener(update);
  }, []);

  return reduced;
}

function easeInOutQuint(t: number) {
  if (t <= 0) return 0;
  if (t >= 1) return 1;
  return t < 0.5
    ? 16 * t * t * t * t * t
    : 1 - Math.pow(-2 * t + 2, 5) / 2;
}

function easeOutCubic(t: number) {
  const clamped = THREE.MathUtils.clamp(t, 0, 1);
  return 1 - Math.pow(1 - clamped, 3);
}

function remapProgress(raw: number) {
  const clamped = THREE.MathUtils.clamp(raw, 0, 1);
  if (clamped <= START_PROGRESS_WINDOW) {
    const local = clamped / Math.max(START_PROGRESS_WINDOW, 1e-5);
    return THREE.MathUtils.lerp(0, 0.32, local);
  }
  if (clamped >= END_PROGRESS_WINDOW) {
    const local = (clamped - END_PROGRESS_WINDOW) /
      Math.max(1 - END_PROGRESS_WINDOW, 1e-5);
    return THREE.MathUtils.lerp(0.72, 1, easeOutCubic(local));
  }
  const local = (clamped - START_PROGRESS_WINDOW) /
    Math.max(END_PROGRESS_WINDOW - START_PROGRESS_WINDOW, 1e-5);
  return THREE.MathUtils.lerp(0.32, 0.72, local);
}

function useScrollRig(depthSpan: number) {
  const reduced = usePrefersReducedMotion();
  const stateRef = useRef({
    target: 0,
    current: 0,
    last: 0,
    velocity: 0,
    max: 1,
  });

  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleScroll = () => {
      stateRef.current.target = window.scrollY;
    };

    const handleResize = () => {
      const maxScroll = Math.max(
        1,
        document.documentElement.scrollHeight - window.innerHeight
      );
      stateRef.current.max = maxScroll;
      stateRef.current.target = Math.min(stateRef.current.target, maxScroll);
    };

    handleResize();
    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const advance = useCallback(
    (delta: number, snapshot: ScrollSnapshot) => {
      const { current, target, last, max, velocity } = stateRef.current;
      stateRef.current.current = THREE.MathUtils.damp(
        current,
        target,
        reduced ? 6 : 12,
        delta
      );
      const rawVelocity =
        (stateRef.current.current - last) / Math.max(delta, 1e-5);
      stateRef.current.velocity = THREE.MathUtils.damp(
        velocity,
        rawVelocity,
        reduced ? 6 : 10,
        delta
      );
      stateRef.current.last = stateRef.current.current;

      const linearProgress =
        max > 0
          ? THREE.MathUtils.clamp(stateRef.current.current / max, 0, 1)
          : 0;
      const stagedProgress = remapProgress(linearProgress);
      const eased = easeInOutQuint(stagedProgress);
      const blended = THREE.MathUtils.lerp(stagedProgress, eased, 0.6);

      snapshot.rawProgress = linearProgress;
      snapshot.progress = blended;
      snapshot.easedProgress = blended;
      snapshot.velocity = stateRef.current.velocity;
      snapshot.depthOffset = THREE.MathUtils.clamp(blended + 0.02, 0, 1.04) * depthSpan;

      return snapshot;
    },
    [reduced, depthSpan]
  );

  return { advance, reduced };
}

function CoinField() {
  const groupRef = useRef<THREE.Group>(null!);
  const spritesRef = useRef<THREE.Sprite[]>([]);
  const glowRef = useRef<THREE.Sprite[]>([]);
  const itemsRef = useRef<Item[]>([]);
  const lastKickRef = useRef<number[]>([]);
  const prevPointerRef = useRef<{ x: number; y: number } | null>(null);
  const frameCounterRef = useRef(0);

  const pointerActiveRef = useRef(false);
  const pointerNormRef = useRef(new THREE.Vector2(0, 0));
  const raycaster = useMemo(() => new THREE.Raycaster(), []);
  const pointerWorld = useMemo(() => new THREE.Vector3(), []);
  const pointerLocal = useMemo(() => new THREE.Vector3(), []);
  const tmpPos = useMemo(() => new THREE.Vector3(), []);
  const planeNormal = useMemo(() => new THREE.Vector3(0, 0, 1), []);
  const plane = useMemo(() => new THREE.Plane(planeNormal.clone(), 0), [planeNormal]);
  const scrollSnapshotRef = useRef<ScrollSnapshot>({
    rawProgress: 0,
    progress: 0,
    easedProgress: 0,
    velocity: 0,
    depthOffset: 0,
  });

  const imageNames = useMemo(
    () => [
      "AAVE.png",
      "Avalanche_Camera1.png",
      "Avax.png",
      "BNB.png",
      "BNB_Camera1.png",
      "BinanceUSD_Camera1.png",
      "Bitcoin.png",
      "Bitcoin_Camera1.png",
      "Cardano.png",
      "Cardano_Camera1.png",
      "Chainlink.png",
      "Cosmohub.png",
      "Cosmos_Camera1.png",
      "Cronos_Camera1.png",
      "DAI.png",
      "Dai_Camera5.png",
      "Dogecoin.png",
      "Dogecoin_Camera1.png",
      "EGLD.png",
      "Ethereum_Camera1.png",
      "Etherium.png",
      "FCTR.png",
      "FTN.png",
      "Filecoin.png",
      "Hashgraph.png",
      "Injective.png",
      "Jupiter.png",
      "KCS.png",
      "Litecoin.png",
      "MKR.png",
      "Mana.png",
      "Near.png",
      "Polkadot.png",
      "Polkadot_Camera1.png",
      "Polygon.png",
      "Polygon_Camera1.png",
      "ShibaInu_Camera1.png",
      "Solana.png",
      "Solana_Camera1.png",
      "Stellar.png",
      "Sushi.png",
      "TerraUSD_Camera1.png",
      "Terra_Camera1.png",
      "Tether.png",
      "Tether_Camera1.png",
      "Ton.png",
      "Tron.png",
      "USDC.png",
      "USDCoin_Camera1.png",
      "Uniswap.png",
      "VET.png",
      "WrappedBitcoin_Camera1.png",
      "XRP.png",
      "XRP_Camera1.png",
      "XTZ.png",
      "ZEC.png",
    ],
    []
  );

  const urls = useMemo(
    () => imageNames.map((name) => `/3D_crypto_coin/${name}`),
    [imageNames]
  );
  const textures = useLoader(THREE.TextureLoader, urls);

  useEffect(() => {
    textures.forEach((texture) => {
      (texture as any).colorSpace =
        THREE.SRGBColorSpace || (THREE as any).SRGBColorSpace;
      texture.anisotropy = 8;
      texture.generateMipmaps = true;
      texture.minFilter = THREE.LinearMipmapLinearFilter;
      texture.magFilter = THREE.LinearFilter;
      texture.needsUpdate = true;
    });
  }, [textures]);

  const materials = useMemo(
    () =>
      textures.map(
        (texture) =>
          new THREE.SpriteMaterial({
            map: texture,
            transparent: true,
            depthWrite: false,
            depthTest: true,
            opacity: 0.95,
            alphaTest: 0.02,
            premultipliedAlpha: true,
          })
      ),
    [textures]
  );

  const glowMaterials = useMemo(
    () =>
      textures.map(
        (texture) =>
          new THREE.SpriteMaterial({
            map: texture,
            color: new THREE.Color("#ffd86b"),
            transparent: true,
            depthWrite: false,
            depthTest: true,
            opacity: 0.35,
            blending: THREE.AdditiveBlending,
          })
      ),
    [textures]
  );

  useEffect(
    () => () => {
      materials.forEach((material) => material.dispose());
      glowMaterials.forEach((material) => material.dispose());
    },
    [materials, glowMaterials]
  );

  const density = 4;
  const total = Math.min(MAX_SPRITES, materials.length * density);
  const indices = useMemo(
    () => Array.from({ length: total }, (_, i) => i % materials.length),
    [materials.length, total]
  );

  const { viewport } = useThree();
  const { advance: advanceScroll, reduced: reducedMotion } = useScrollRig(
    DEPTH_SPAN
  );

  useEffect(() => {
    if (typeof window === "undefined") return;

    const updatePointer = (event: PointerEvent | TouchEvent | any) => {
      let clientX: number | null = null;
      let clientY: number | null = null;

      const isTouch = (evt: any): evt is TouchEvent =>
        typeof evt === 'object' && (('touches' in evt) || ('changedTouches' in evt));

      if (isTouch(event)) {
        const t = event.touches && event.touches.length > 0
          ? event.touches[0]
          : event.changedTouches && event.changedTouches.length > 0
          ? event.changedTouches[0]
          : null;
        if (t) {
          clientX = t.clientX;
          clientY = t.clientY;
        }
      } else {
        clientX = (event as PointerEvent).clientX;
        clientY = (event as PointerEvent).clientY;
      }

      if (clientX === null || clientY === null) return;
      pointerNormRef.current.set(
        (clientX / window.innerWidth) * 2 - 1,
        -(clientY / window.innerHeight) * 2 + 1
      );
      pointerActiveRef.current = true;
    };

    const onPointerMove = (event: PointerEvent) => updatePointer(event);
    const onPointerLeave = () => (pointerActiveRef.current = false);
    const onTouchMove = (event: any) => updatePointer(event);
    const onTouchEnd = () => (pointerActiveRef.current = false);

    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerleave", onPointerLeave, { passive: true });
    window.addEventListener("blur", onPointerLeave);
    window.addEventListener("touchmove", onTouchMove, { passive: true });
    window.addEventListener("touchend", onTouchEnd, { passive: true });
    window.addEventListener("touchcancel", onTouchEnd, { passive: true });

    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerleave", onPointerLeave);
      window.removeEventListener("blur", onPointerLeave);
      window.removeEventListener("touchmove", onTouchMove);
      window.removeEventListener("touchend", onTouchEnd);
      window.removeEventListener("touchcancel", onTouchEnd);
    };
  }, []);

  useEffect(() => {
    const w = viewport.width;
    const h = viewport.height;
    const spreadX = w * 0.95;
    const spreadY = h * 1.05;
    const depthJitter = DEPTH_SPAN * 0.12;

    itemsRef.current = indices.map((_, index) => {
      const depthSeed = DEPTH_FAR + Math.pow(Math.random(), 0.72) * DEPTH_SPAN;
      const depthBias = THREE.MathUtils.lerp(-depthJitter, depthJitter, Math.random());
      const depth = THREE.MathUtils.clamp(depthSeed + depthBias, DEPTH_FAR, DEPTH_NEAR);
      const depthLerp = THREE.MathUtils.clamp(
        (depth - DEPTH_FAR) / DEPTH_SPAN,
        0,
        1
      );
      const radiusNorm = Math.sqrt((index + 0.5) / indices.length);
      const baseAngle = index * GOLDEN_ANGLE;
      const jitterAngle = baseAngle + (Math.random() - 0.5) * 0.28;
      const jitterRadius = THREE.MathUtils.lerp(0.92, 1.08, Math.random());
      const baseRadius = radiusNorm * jitterRadius;
      const ellipseX = Math.cos(jitterAngle) * baseRadius * spreadX;
      const ellipseY = Math.sin(jitterAngle) * baseRadius * spreadY;
      const base = new THREE.Vector3(
        ellipseX,
        ellipseY,
        depth
      );
      const orbitT = THREE.MathUtils.clamp(radiusNorm * 1.05, 0, 1);
      const orbitRadius = Math.max(spreadX, spreadY) * THREE.MathUtils.lerp(
        0.18,
        0.86,
        orbitT
      ) * THREE.MathUtils.lerp(0.82, 1.18, Math.random());
      return {
        base,
        ampX: 0.38 + Math.random() * 0.82,
        ampY: 0.36 + Math.random() * 0.76,
        speedX: 0.15 + Math.random() * 0.28,
        speedY: 0.13 + Math.random() * 0.25,
        phaseX: Math.random() * Math.PI * 2,
        phaseY: Math.random() * Math.PI * 2,
        driftX: (Math.random() - 0.5) * 0.22,
        driftY: (Math.random() - 0.5) * 0.22,
        rot: (Math.random() - 0.5) * 0.7,
        scale: THREE.MathUtils.lerp(0.35, 0.82, 1 - depthLerp),
        depth,
        twinkle: Math.random() * Math.PI * 2,
        orbitRadius,
        orbitPhase: baseAngle + Math.random() * 0.6,
        orbitTilt: THREE.MathUtils.lerp(-0.5, 0.5, Math.random()),
        orbitSpeed: THREE.MathUtils.lerp(0.058, 0.21, Math.random()),
      } satisfies Item;
    });

    spritesRef.current.forEach((sprite, index) => {
      const item = itemsRef.current[index];
      if (!sprite || !item) return;
      sprite.position.copy(item.base);
      sprite.scale.setScalar(item.scale);
      const glow = glowRef.current[index];
      if (glow) {
        glow.position.copy(item.base);
        glow.scale.setScalar(item.scale * 1.45);
      }
    });

    lastKickRef.current = new Array(indices.length).fill(0);
    prevPointerRef.current = null;
  }, [indices, viewport.width, viewport.height]);

  useFrame((state, delta) => {
    const scroll = advanceScroll(delta, scrollSnapshotRef.current);
    const depthOffset = reducedMotion
      ? scroll.rawProgress * DEPTH_SPAN * 0.42
      : scroll.depthOffset;

    const w = state.viewport.width;
    const h = state.viewport.height;
    const t = state.clock.elapsedTime;
    const velocityBoost = THREE.MathUtils.clamp(
      Math.abs(scroll.velocity) * 0.0004,
      0,
      0.45
    );
    const repelRadius = Math.min(w, h) * 0.26;
    const repelStrength = 2.4 + velocityBoost * 2.6;
    const swirlDrift = depthOffset * 0.09;

    if (groupRef.current) {
      const parallaxX = pointerActiveRef.current
        ? pointerNormRef.current.x * 0.55
        : 0;
      const parallaxY = pointerActiveRef.current
        ? pointerNormRef.current.y * 0.4
        : -scroll.progress * 0.6;
      groupRef.current.position.x = THREE.MathUtils.damp(
        groupRef.current.position.x,
        parallaxX,
        12,
        delta
      );
      groupRef.current.position.y = THREE.MathUtils.damp(
        groupRef.current.position.y,
        parallaxY,
        12,
        delta
      );
      const targetZ = -2.4 - scroll.progress * 1.35;
      groupRef.current.position.z = THREE.MathUtils.damp(
        groupRef.current.position.z,
        targetZ,
        16,
        delta
      );
    }

    const easedCamera = easeOutCubic(scroll.progress);
    const cameraTargetZ = THREE.MathUtils.lerp(6, 3.25, easedCamera);
    const cameraTargetY = THREE.MathUtils.lerp(1.2, 0.25, easedCamera);
    state.camera.position.z = THREE.MathUtils.damp(
      state.camera.position.z,
      cameraTargetZ,
      reducedMotion ? 4 : 7,
      delta
    );
    state.camera.position.y = THREE.MathUtils.damp(
      state.camera.position.y,
      cameraTargetY,
      reducedMotion ? 4 : 6,
      delta
    );

    if (groupRef.current) {
      groupRef.current.getWorldPosition(tmpPos);
      plane.set(planeNormal, -tmpPos.z);
    }

    let repelEnabled = false;
    let localMX = 0;
    let localMY = 0;

    if (groupRef.current) {
      raycaster.setFromCamera(pointerNormRef.current, state.camera);
      const hit = raycaster.ray.intersectPlane(plane, pointerWorld);
      if (hit) {
        pointerLocal.copy(pointerWorld);
        groupRef.current.worldToLocal(pointerLocal);
        localMX = pointerLocal.x;
        localMY = pointerLocal.y;
        repelEnabled = pointerActiveRef.current;
      }
    }

    let pointerVelocity = 0;
    if (repelEnabled) {
      const prev = prevPointerRef.current;
      if (prev) {
        const dx = localMX - prev.x;
        const dy = localMY - prev.y;
        pointerVelocity = Math.hypot(dx, dy) / Math.max(delta, 1e-3);
      }
      prevPointerRef.current = { x: localMX, y: localMY };
    } else {
      prevPointerRef.current = null;
    }

    const neighborRadius = w * 1.5;
    const neighborHeight = h * 1.6;

    for (let i = 0; i < spritesRef.current.length; i++) {
      const sprite = spritesRef.current[i];
      const item = itemsRef.current[i];
      if (!sprite || !item) continue;

      const depthWrapped =
        DEPTH_FAR +
        THREE.MathUtils.euclideanModulo(
          item.depth + depthOffset - DEPTH_FAR,
          DEPTH_SPAN
        );
      const depthFactor = THREE.MathUtils.clamp(
        (depthWrapped - DEPTH_FAR) / DEPTH_SPAN,
        0,
        1
      );

      const orbitAngle =
        t * item.orbitSpeed + swirlDrift + item.orbitPhase;
      const orbitRadius = THREE.MathUtils.lerp(
        item.orbitRadius * 0.6,
        item.orbitRadius,
        1 - Math.pow(depthFactor, 1.3)
      );

      const oscX =
        Math.sin(t * item.speedX + item.phaseX) * item.ampX +
        Math.sin((t + item.phaseY) * 0.15) * item.driftX * 6;
      const oscY =
        Math.cos(t * item.speedY + item.phaseY) * item.ampY +
        Math.cos((t + item.phaseX) * 0.12) * item.driftY * 6;

      const baseX =
        item.base.x +
        Math.cos(orbitAngle) * orbitRadius +
        oscX;
      const baseY =
        item.base.y +
        Math.sin(orbitAngle) * orbitRadius * 0.62 +
        oscY +
        depthFactor * item.orbitTilt * h * 0.28;

      let px = baseX;
      let py = baseY;

      const dx = px - localMX;
      const dy = py - localMY;
      const distSq = dx * dx + dy * dy;
      const threshold = repelRadius * repelRadius;
      if (distSq < threshold && distSq > 1e-4 && repelEnabled) {
        const dist = Math.sqrt(distSq);
        const nx = dx / dist;
        const ny = dy / dist;
        const falloff = 1 - dist / repelRadius;
        const impulse =
          (repelStrength + (pointerVelocity + Math.abs(scroll.velocity)) * 0.001)
          * falloff;

        px += nx * impulse;
        py += ny * impulse;

        const now = state.clock.elapsedTime;
        if (now - (lastKickRef.current[i] || 0) > REPULSE_COOLDOWN) {
          lastKickRef.current[i] = now;
          gsap.to(item.base, {
            x: item.base.x + nx * impulse * 0.7,
            y: item.base.y + ny * impulse * 0.7,
            duration: 0.28,
            ease: "expo.out",
            overwrite: true,
          });
          const punch = Math.min(1.28, 1 + falloff * 0.42);
          gsap.to(sprite.scale, {
            x: sprite.scale.x * punch,
            y: sprite.scale.y * punch,
            duration: 0.12,
            yoyo: true,
            repeat: 1,
            ease: "sine.inOut",
            overwrite: true,
          });
          const glow = glowRef.current[i];
          if (glow) {
            gsap.to(glow.material as THREE.SpriteMaterial, {
              opacity: Math.min(0.75, 0.4 + falloff * 0.8),
              duration: 0.14,
              yoyo: true,
              repeat: 1,
              ease: "sine.inOut",
              overwrite: true,
            });
          }
        }
      }

      sprite.position.set(px, py, depthWrapped);
      const glowSprite = glowRef.current[i];
      if (glowSprite) {
        glowSprite.position.set(px, py, depthWrapped - 0.001);
      }

      if (item.base.x < -neighborRadius) item.base.x += neighborRadius * 2;
      else if (item.base.x > neighborRadius) item.base.x -= neighborRadius * 2;
      if (item.base.y < -neighborHeight) item.base.y += neighborHeight * 2;
      else if (item.base.y > neighborHeight) item.base.y -= neighborHeight * 2;

      const material = sprite.material as THREE.SpriteMaterial;
      const twinkle = 0.85 + Math.sin(t * 1.1 + item.twinkle) * 0.14;
      const perspectiveScale = THREE.MathUtils.lerp(1.9, 0.75, depthFactor);
      const velocityScale = 1 + velocityBoost * 0.8;
      const scale = item.scale * perspectiveScale * twinkle * velocityScale;

      sprite.scale.setScalar(scale);
      material.rotation += item.rot * delta;
      material.opacity = THREE.MathUtils.clamp(
        0.65 + (1 - depthFactor) * 0.28 + velocityBoost * 0.22,
        0.45,
        1
      );

      if (glowSprite) {
        const glowMaterial = glowSprite.material as THREE.SpriteMaterial;
        glowSprite.scale.setScalar(scale * 1.45);
        glowMaterial.opacity = THREE.MathUtils.clamp(
          0.16 + (1 - depthFactor) * 0.32 + velocityBoost * 0.55,
          0.12,
          0.9
        );
      }
    }

    frameCounterRef.current = (frameCounterRef.current + 1) % COLLISION_FRAME_STEP;
    if (frameCounterRef.current === 0) {
      const cellSize = 1.05;
      const cols = Math.ceil((w * 2.4) / cellSize);
      const rows = Math.ceil((h * 2.2) / cellSize);
      const buckets: number[][] = Array.from({ length: cols * rows }, () => []);

      const toCellIndex = (x: number, y: number) => {
        const cx = Math.floor((x + w * 1.2) / cellSize);
        const cy = Math.floor((y + h * 1.1) / cellSize);
        if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) return -1;
        return cy * cols + cx;
      };

      for (let i = 0; i < spritesRef.current.length; i++) {
        const sprite = spritesRef.current[i];
        if (!sprite) continue;
        const index = toCellIndex(sprite.position.x, sprite.position.y);
        if (index >= 0) buckets[index].push(i);
      }

      const neighborOffsets = [
        0,
        1,
        -1,
        cols,
        -cols,
        cols + 1,
        cols - 1,
        -cols + 1,
        -cols - 1,
      ];

      for (let baseY = 0; baseY < rows; baseY++) {
        for (let baseX = 0; baseX < cols; baseX++) {
          const baseIdx = baseY * cols + baseX;
          const candidates: number[] = [];
          for (const offset of neighborOffsets) {
            const bucketIndex = baseIdx + offset;
            if (bucketIndex < 0 || bucketIndex >= buckets.length) continue;
            const bucket = buckets[bucketIndex];
            for (let i = 0; i < bucket.length; i++) {
              const idx = bucket[i];
              if (candidates.indexOf(idx) !== -1) continue;
              candidates.push(idx);
            }
          }
          for (let a = 0; a < candidates.length; a++) {
            for (let b = a + 1; b < candidates.length; b++) {
              const i1 = candidates[a];
              const i2 = candidates[b];
              const s1 = spritesRef.current[i1];
              const s2 = spritesRef.current[i2];
              if (!s1 || !s2) continue;
              const it1 = itemsRef.current[i1];
              const it2 = itemsRef.current[i2];
              if (!it1 || !it2) continue;
              const dx = s2.position.x - s1.position.x;
              const dy = s2.position.y - s1.position.y;
              const distanceSq = dx * dx + dy * dy;
              const radius1 = s1.scale.x * 0.36;
              const radius2 = s2.scale.x * 0.36;
              const minDistance = radius1 + radius2;
              if (distanceSq > minDistance * minDistance || distanceSq < 1e-6)
                continue;
              const distance = Math.sqrt(distanceSq);
              const nx = dx / distance;
              const ny = dy / distance;
              const overlap = minDistance - distance + 0.02;
              const push = overlap * 0.6;

              gsap.to(it1.base, {
                x: it1.base.x - nx * push,
                y: it1.base.y - ny * push,
                duration: 0.25,
                ease: "sine.out",
                overwrite: true,
              });
              gsap.to(it2.base, {
                x: it2.base.x + nx * push,
                y: it2.base.y + ny * push,
                duration: 0.25,
                ease: "sine.out",
                overwrite: true,
              });
            }
          }
        }
      }
    }
  });

  return (
    <group ref={groupRef} position={[0, 0, -2.4]}>
      {indices.map((materialIndex, index) => (
        <group key={index}>
          <sprite
            ref={(el) => {
              if (el) {
                glowRef.current[index] = el as THREE.Sprite;
              }
            }}
            material={glowMaterials[materialIndex]}
            position={[0, 0, -2.401]}
          />
          <sprite
            ref={(el) => {
              if (el) {
                spritesRef.current[index] = el as THREE.Sprite;
              }
            }}
            material={materials[materialIndex]}
            position={[0, 0, -2.4]}
          />
        </group>
      ))}
    </group>
  );
}
