"use client";

import React, { useMemo, useRef, useEffect } from "react";
import * as THREE from "three";
import { useFrame, useThree, useLoader } from "@react-three/fiber";
import gsap from "gsap";

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
};

function CoinField() {
  const groupRef = useRef<THREE.Group>(null!);
  const spritesRef = useRef<THREE.Sprite[]>([]); // main coins
  const glowRef = useRef<THREE.Sprite[]>([]);    // glow sprites
  const itemsRef = useRef<Item[]>([]);
  const lastKickRef = useRef<number[]>([]);
  const prevMouseRef = useRef<{x:number;y:number}|null>(null);

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

  const urls = useMemo(() => imageNames.map((n) => `/3D_crypto_coin/${n}`), [imageNames]);
  const textures = useLoader(THREE.TextureLoader, urls);

  useEffect(() => {
    textures.forEach((t) => {
      // Ensure vivid color sampling
      // @ts-ignore - colorSpace available in our three version
      t.colorSpace = THREE.SRGBColorSpace || (THREE as any).SRGBColorSpace;
      t.anisotropy = 8;
      t.generateMipmaps = true;
      t.minFilter = THREE.LinearMipmapLinearFilter;
      t.magFilter = THREE.LinearFilter;
      t.needsUpdate = true;
    });
  }, [textures]);

  // Main material (crisp) + glow material (additive)
  const materials = useMemo(() => textures.map((tex) => new THREE.SpriteMaterial({
    map: tex,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    opacity: 0.95,
    alphaTest: 0.02,
    premultipliedAlpha: true,
  })), [textures]);

  const glowMaterials = useMemo(() => textures.map((tex) => new THREE.SpriteMaterial({
    map: tex,
    color: new THREE.Color('#ffd86b'),
    transparent: true,
    depthWrite: false,
    depthTest: true,
    opacity: 0.35,
    blending: THREE.AdditiveBlending,
  })), [textures]);

  useEffect(() => () => {
    materials.forEach((m) => m.dispose());
    glowMaterials.forEach((m) => m.dispose());
  }, [materials, glowMaterials]);

  // Slightly higher density so edges/bottom feel filled
  const density = 4; // sprites per texture
  const total = Math.min(320, materials.length * density);
  const indices = useMemo(() => Array.from({ length: total }, (_, i) => i % materials.length), [materials.length, total]);

  const { viewport, gl } = useThree();
  const pointerActiveRef = useRef(false);

  useEffect(() => {
    const el = gl.domElement as HTMLElement;
    const onEnter = () => (pointerActiveRef.current = true);
    const onMove = () => (pointerActiveRef.current = true);
    const onLeave = () => (pointerActiveRef.current = false);
    const onTouchStart = () => (pointerActiveRef.current = true);
    const onTouchEnd = () => (pointerActiveRef.current = false);
    el.addEventListener('pointerenter', onEnter);
    el.addEventListener('pointermove', onMove);
    el.addEventListener('pointerleave', onLeave);
    el.addEventListener('touchstart', onTouchStart, { passive: true });
    el.addEventListener('touchend', onTouchEnd, { passive: true });
    return () => {
      el.removeEventListener('pointerenter', onEnter);
      el.removeEventListener('pointermove', onMove);
      el.removeEventListener('pointerleave', onLeave);
      el.removeEventListener('touchstart', onTouchStart as any);
      el.removeEventListener('touchend', onTouchEnd as any);
    };
  }, [gl.domElement]);

  useEffect(() => {
    const w = viewport.width;
    const h = viewport.height;
    // depth layering front to back (~-1.8 .. -2.8) for consistent sizing
    itemsRef.current = indices.map((matIndex, i) => {
      const depth = -1.8 - Math.random() * 1.0;
      const scaleDepth = THREE.MathUtils.mapLinear(depth, -1.4, -3.0, 1.0, 0.6);
      // Broader spawn area (especially Y) so bottom fills well
      const base = new THREE.Vector3((Math.random() - 0.5) * w * 1.8, (Math.random() - 0.5) * h * 2.2, depth);
      return {
        base,
        ampX: 0.5 + Math.random() * 0.9,
        ampY: 0.4 + Math.random() * 0.8,
        speedX: 0.15 + Math.random() * 0.25,
        speedY: 0.12 + Math.random() * 0.22,
        phaseX: Math.random() * Math.PI * 2,
        phaseY: Math.random() * Math.PI * 2,
        driftX: (Math.random() - 0.5) * 0.15,
        driftY: (Math.random() - 0.5) * 0.15,
        rot: (Math.random() - 0.5) * 0.7,
        scale: (0.35 + Math.random() * 0.45) * scaleDepth,
        depth,
        twinkle: Math.random() * Math.PI * 2,
      } as Item;
    });

    // seed initial positions if sprites already mounted
    spritesRef.current.forEach((s, i) => {
      const it = itemsRef.current[i];
      if (s && it) {
        s.position.copy(it.base);
        s.scale.setScalar(it.scale);
      }
    });
    lastKickRef.current = new Array(indices.length).fill(0);
    prevMouseRef.current = null;
  }, [indices, viewport.width, viewport.height]);

  useFrame((state, delta) => {
    const w = state.viewport.width;
    const h = state.viewport.height;
    let mouseX = state.pointer.x * (w / 2);
    let mouseY = state.pointer.y * (h / 2);
    const repelRadius = Math.min(w, h) * 0.3; // slightly smaller to avoid large voids
    const repelStrength = 2.2;
    const t = state.clock.elapsedTime;

    // Disable repel when pointer not active to prevent a permanent void at center
    const repelEnabled = pointerActiveRef.current === true;
    if (!repelEnabled) {
      mouseX = 99999;
      mouseY = 99999;
    }

    // Parallax group motion
    if (groupRef.current) {
      const targetX = repelEnabled ? state.pointer.x * 0.25 : 0;
      const targetY = repelEnabled ? -state.pointer.y * 0.18 : 0;
      groupRef.current.position.x = THREE.MathUtils.lerp(groupRef.current.position.x, targetX, 0.06);
      groupRef.current.position.y = THREE.MathUtils.lerp(groupRef.current.position.y, targetY, 0.06);
      groupRef.current.position.z = -2.2;
    }

    // track pointer velocity to scale the "throw"
    let mouseV = 0;
    if (repelEnabled) {
      const prev = prevMouseRef.current;
      if (prev) {
        const ddx = mouseX - prev.x;
        const ddy = mouseY - prev.y;
        mouseV = Math.hypot(ddx, ddy) / Math.max(1e-3, delta);
      }
      prevMouseRef.current = { x: mouseX, y: mouseY };
    } else {
      prevMouseRef.current = null;
    }

    for (let i = 0; i < spritesRef.current.length; i++) {
      const s = spritesRef.current[i];
      const it = itemsRef.current[i];
      if (!s || !it) continue;

      const px = it.base.x + Math.sin(t * it.speedX + it.phaseX) * it.ampX + Math.sin((t + it.phaseY) * 0.12) * it.driftX * 10;
      const py = it.base.y + Math.cos(t * it.speedY + it.phaseY) * it.ampY + Math.cos((t + it.phaseX) * 0.1) * it.driftY * 10;
      const pz = it.depth;

      // pointer repel
      let ox = px, oy = py;
      const dx = px - mouseX;
      const dy = py - mouseY;
      const d2 = dx * dx + dy * dy;
      const r2 = repelRadius * repelRadius;
      if (d2 < r2 && d2 > 1e-4 && repelEnabled) {
        const d = Math.sqrt(d2);
        const nx = dx / d;
        const ny = dy / d;
        const falloff = (1 - d / repelRadius);
        const impulse = (repelStrength + mouseV * 0.0015) * falloff; // scale with pointer speed

        // do an immediate offset for responsiveness
        ox += nx * impulse;
        oy += ny * impulse;

        // and tween the base so the trajectory continues naturally
        const now = state.clock.elapsedTime;
        if (now - (lastKickRef.current[i] || 0) > 0.12) {
          lastKickRef.current[i] = now;
          gsap.to(it.base, {
            x: it.base.x + nx * impulse * 0.8,
            y: it.base.y + ny * impulse * 0.8,
            duration: 0.28,
            ease: "expo.out",
            overwrite: true,
          });
          // quick punch scale for feedback
          const punch = Math.min(1.25, 1 + falloff * 0.35);
          gsap.to(s.scale, { x: s.scale.x * punch, y: s.scale.y * punch, duration: 0.12, yoyo: true, repeat: 1, ease: "sine.inOut", overwrite: true });
          const g = glowRef.current[i];
          if (g) gsap.to((g.material as THREE.SpriteMaterial), { opacity: 0.55, duration: 0.12, yoyo: true, repeat: 1, ease: "sine.inOut", overwrite: true });
        }
      }

      s.position.set(ox, oy, pz);
      const g = glowRef.current[i];
      if (g) {
        g.position.set(ox, oy, pz - 0.001);
      }

      // wrap-around bounds so coins fill full screen rather than clustering center
      const bx = w * 1.1;
      const by = h * 1.25; // allow wrapping beyond bottom to keep it populated
      if (ox < -bx) it.base.x += bx * 2;
      else if (ox > bx) it.base.x -= bx * 2;
      if (oy < -by) it.base.y += by * 2;
      else if (oy > by) it.base.y -= by * 2;

      // rotation + scale/opacity twinkle
      const mat = s.material as THREE.SpriteMaterial;
      mat.rotation += it.rot * delta;
      const tw = 0.85 + Math.sin(t * 0.9 + it.twinkle) * 0.12;
      mat.opacity = 0.75 + (1 - (Math.abs(pz) - 1.4) / 1.6) * 0.15; // slightly brighter when nearer
      const sc = it.scale * tw;
      s.scale.setScalar(sc);
      if (g) g.scale.setScalar(sc * 1.45);
    }

    // Broad-phase grid for overlap resolution using GSAP
    const cell = 0.9; // world units grid cell
    const cols = Math.ceil((w * 2.2) / cell);
    const rows = Math.ceil((h * 2.0) / cell);
    const buckets: number[][] = Array(cols * rows).fill(null).map(() => []);

    function cellIndex(x: number, y: number) {
      const cx = Math.floor((x + w * 1.1) / cell);
      const cy = Math.floor((y + h * 1.0) / cell);
      if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) return -1;
      return cy * cols + cx;
    }

    // Fill buckets
    for (let i = 0; i < spritesRef.current.length; i++) {
      const s = spritesRef.current[i];
      if (!s) continue;
      const idx = cellIndex(s.position.x, s.position.y);
      if (idx >= 0) buckets[idx].push(i);
    }

    const now = t;
    // Resolve overlaps in each bucket and neighbors
    const neighborOffsets = [0, 1, -1, cols, -cols, cols+1, cols-1, -cols+1, -cols-1];
    for (let by = 0; by < rows; by++) {
      for (let bx = 0; bx < cols; bx++) {
        const baseIdx = by * cols + bx;
        let candidates: number[] = [];
        for (const off of neighborOffsets) {
          const bi = baseIdx + off;
          if (bi >= 0 && bi < buckets.length) candidates = candidates.concat(buckets[bi]);
        }
        // de-dup (small arrays)
        candidates = Array.from(new Set(candidates));
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
            const dist2 = dx*dx + dy*dy;
            const r1 = s1.scale.x * 0.35;
            const r2 = s2.scale.x * 0.35;
            const rsum = r1 + r2;
            if (dist2 > rsum * rsum || dist2 < 1e-6) continue;
            const dist = Math.sqrt(dist2);
            const nx = dx / dist;
            const ny = dy / dist;
            const overlap = rsum - dist + 0.02;
            const push = overlap * 0.6;

            // Use gsap to separate their bases smoothly (so motion continues naturally)
            gsap.to(it1.base, { x: it1.base.x - nx * push, y: it1.base.y - ny * push, duration: 0.25, ease: "sine.out" });
            gsap.to(it2.base, { x: it2.base.x + nx * push, y: it2.base.y + ny * push, duration: 0.25, ease: "sine.out" });
          }
        }
      }
    }
  });

  return (
    <group ref={groupRef} position={[0, 0, -2.2]}>
      {indices.map((matIndex, i) => (
        <group key={i}>
          <sprite
            ref={(el) => (glowRef.current[i] = el as THREE.Sprite)}
            material={glowMaterials[matIndex]}
            position={[0, 0, -2.201]}
            scale={[0.7, 0.7, 0.7]}
          />
          <sprite
            ref={(el) => (spritesRef.current[i] = el as THREE.Sprite)}
            material={materials[matIndex]}
            position={[0, 0, -2.2]}
            scale={[0.5, 0.5, 0.5]}
          />
        </group>
      ))}
    </group>
  );
}
