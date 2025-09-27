"use client";

import React, { useMemo, useRef, useEffect } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { Text } from "@react-three/drei";

const CYCLE_DURATION = 7;
const PHASES = [
  { name: "influx" as const, start: 0, duration: 2 },
  { name: "core" as const, start: 2, duration: 2 },
  { name: "pulse" as const, start: 4, duration: 1 },
  { name: "execution" as const, start: 5, duration: 2 },
];

type PhaseName = (typeof PHASES)[number]["name"];

type PhaseInfo = {
  name: PhaseName;
  progress: number;
  cycleTime: number;
};

function getPhaseInfo(elapsed: number): PhaseInfo {
  const mod = elapsed % CYCLE_DURATION;
  for (const phase of PHASES) {
    const end = phase.start + phase.duration;
    if (mod >= phase.start && mod < end) {
      return {
        name: phase.name,
        progress: (mod - phase.start) / phase.duration,
        cycleTime: mod,
      };
    }
  }
  return { name: "execution", progress: 0, cycleTime: mod };
}

const COLOR_POSITIVE = new THREE.Color("#22c55e");
const COLOR_NEGATIVE = new THREE.Color("#f87171");
const COLOR_POS_EMISSIVE = new THREE.Color("#34d399");
const COLOR_NEG_EMISSIVE = new THREE.Color("#7f1d1d");
const COLOR_LATTICE = new THREE.Color("#38bdf8");
const COLOR_BEAM = new THREE.Color("#facc15");

type GroupProps = JSX.IntrinsicElements["group"];

const GroupPrimitive = React.forwardRef<THREE.Group, GroupProps>(({ children, ...rest }, ref) =>
  React.createElement("group", { ...rest, ref }, children)
);

GroupPrimitive.displayName = "GroupPrimitive";

export default function Scene() {
  return (
    <>
      <color attach="background" args={["#01040b"]} />
      <fog attach="fog" args={["#01040b", 15, 50]} />
      <Lights />
      <SceneContent />
    </>
  );
}

function Lights() {
  return (
    <>
      <ambientLight intensity={0.35} />
      <directionalLight position={[5, 6, 5]} intensity={1.4} color="#facc15" castShadow />
      <pointLight position={[-4, 2, -3]} intensity={0.7} color="#38bdf8" />
      <pointLight position={[2, 3, -6]} intensity={0.6} color="#22d3ee" />
    </>
  );
}

function SceneContent() {
  const groupRef = useRef<THREE.Group>(null!);

  useFrame(({ clock }) => {
    if (!groupRef.current) return;
    const t = clock.getElapsedTime();
    groupRef.current.rotation.y = Math.sin(t * 0.12) * 0.08;
    groupRef.current.rotation.x = Math.cos(t * 0.18) * 0.04;
  });

  return (
    <GroupPrimitive ref={groupRef}>
      <Atmosphere />
      <DataStreams />
      <NeuralCore />
      <PhasePulse />
      <CandlestickField />
      <PriceTrail />
      <ExecutionBeam />
      <HeroTitle />
    </GroupPrimitive>
  );
}

function Atmosphere() {
  const pointsRef = useRef<THREE.Points>(null!);
  const positions = useMemo(() => {
    const count = 420;
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const radius = 7 + Math.random() * 14;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(THREE.MathUtils.randFloatSpread(2));
      arr[i * 3 + 0] = radius * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      arr[i * 3 + 2] = radius * Math.cos(phi) - 3;
    }
    return arr;
  }, []);

  useFrame(({ clock }) => {
    if (!pointsRef.current) return;
    pointsRef.current.rotation.y = clock.elapsedTime * 0.03;
  });

  return (
    <points ref={pointsRef} frustumCulled>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={positions.length / 3} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial color="#1e3a8a" size={0.04} sizeAttenuation opacity={0.45} transparent depthWrite={false} />
    </points>
  );
}

type StreamConfig = {
  direction: THREE.Vector3;
  spreadY: number;
  spreadZ: number;
  color: string;
  offset: THREE.Vector3;
};

function DataStreams() {
  const geometry = useMemo(() => new THREE.BoxGeometry(0.32, 1, 0.32), []);
  const configs: StreamConfig[] = useMemo(
    () => [
      { direction: new THREE.Vector3(-1, 0.12, 0), spreadY: 1.6, spreadZ: 2.8, color: "#38bdf8", offset: new THREE.Vector3(0, 0.2, -1) },
      { direction: new THREE.Vector3(1, -0.12, 0.2), spreadY: 1.4, spreadZ: 2.6, color: "#22d3ee", offset: new THREE.Vector3(0, 0.3, -1) },
      { direction: new THREE.Vector3(0, 1, -0.4), spreadY: 1.2, spreadZ: 2.3, color: "#f59e0b", offset: new THREE.Vector3(0, 0.3, -1.4) },
      { direction: new THREE.Vector3(0, -1, 0.2), spreadY: 1.8, spreadZ: 2.6, color: "#38bdf8", offset: new THREE.Vector3(0, 0.3, -1.2) },
    ],
    []
  );

  return (
    <GroupPrimitive>
      {configs.map((cfg, idx) => (
        <StreamGroup key={idx} geometry={geometry} {...cfg} />
      ))}
    </GroupPrimitive>
  );
}

function StreamGroup({ geometry, direction, spreadY, spreadZ, color, offset, count = 60 }: StreamConfig & { geometry: THREE.BoxGeometry; count?: number }) {
  const material = useMemo(() => new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.82 }), []);
  const meshRef = useRef<THREE.InstancedMesh>(null!);
  const dummy = useMemo(() => new THREE.Object3D(), []);
  const offsets = useMemo(() => Float32Array.from({ length: count }, () => Math.random()), [count]);
  const jitter = useMemo(
    () =>
      Array.from({ length: count }, () => ({
        y: (Math.random() - 0.5) * spreadY,
        z: (Math.random() - 0.5) * spreadZ,
      })),
    [count, spreadY, spreadZ]
  );
  const dir = useMemo(() => direction.clone().normalize(), [direction]);
  const colorVec = useMemo(() => new THREE.Color(color), [color]);

  useEffect(() => {
    material.vertexColors = true;
    material.color.setScalar(1);
  }, [material]);

  useEffect(() => {
    if (!meshRef.current) return;
    for (let i = 0; i < count; i++) {
      meshRef.current.setColorAt(i, colorVec);
    }
    meshRef.current.instanceColor!.needsUpdate = true;
  }, [count, colorVec]);

  useFrame(({ clock }) => {
    const info = getPhaseInfo(clock.getElapsedTime());
    const base = (clock.getElapsedTime() * 0.2) % 1;
    let activation = 0;
    if (info.name === "influx") activation = THREE.MathUtils.smoothstep(info.progress, 0, 1);
    else if (info.name === "core") activation = THREE.MathUtils.lerp(1, 0, info.progress);
    else activation = 0;

    for (let i = 0; i < count; i++) {
      const travel = (base + offsets[i]) % 1;
      const dist = THREE.MathUtils.lerp(7.5, 0.4, travel);
      const j = jitter[i];
      const visible = activation > 0.02;
      const scaleFactor = visible ? THREE.MathUtils.lerp(0.45, 0.08, travel) * activation : 0.001;
      dummy.position.set(offset.x + dir.x * dist, offset.y + dir.y * dist + j.y, offset.z + dir.z * dist + j.z);
      dummy.scale.set(scaleFactor * 0.35, Math.max(scaleFactor * 2.2, 0.001), scaleFactor * 0.35);
      dummy.lookAt(offset.x, offset.y, offset.z);
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    }
    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  return <instancedMesh ref={meshRef} args={[geometry, material, count]} frustumCulled={false} />;
}

function NeuralCore() {
  const shellRef = useRef<THREE.Mesh>(null!);
  const latticeRef = useRef<THREE.LineSegments>(null!);
  const auraRef = useRef<THREE.Mesh>(null!);

  const latticeGeometry = useMemo(() => {
    const segments = 160;
    const positions = new Float32Array(segments * 2 * 3);
    for (let i = 0; i < segments; i++) {
      const start = randomPointInSphere(0.85);
      const end = start.clone().multiplyScalar(THREE.MathUtils.lerp(0.35, 0.75, Math.random()));
      positions.set(start.toArray(), i * 6 + 0);
      positions.set(end.toArray(), i * 6 + 3);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return geo;
  }, []);

  useFrame(({ clock }) => {
    const info = getPhaseInfo(clock.getElapsedTime());
    const shell = shellRef.current;
    const lattice = latticeRef.current;
    const aura = auraRef.current;
    if (!shell || !lattice || !aura) return;

    const shellMat = shell.material as THREE.MeshStandardMaterial;
    const latticeMat = lattice.material as THREE.LineBasicMaterial;
    const auraMat = aura.material as THREE.MeshBasicMaterial;

    let activation = 0;
    if (info.name === "influx") activation = THREE.MathUtils.smoothstep(info.progress, 0, 1);
    else activation = 1;

    const pulse = info.name === "pulse" ? THREE.MathUtils.smoothstep(info.progress, 0, 1) : info.name === "execution" ? THREE.MathUtils.lerp(1, 0.2, info.progress) : 0;

    const scale = THREE.MathUtils.lerp(0.55, 1.05, activation) + pulse * 0.12;
    shell.scale.setScalar(scale);
    lattice.scale.setScalar(scale * 0.92);
    aura.scale.setScalar(scale * 1.35 + pulse * 0.1);

    const emissiveIntensity = 0.35 + activation * 0.35 + pulse * 1.2;
    shellMat.emissive.copy(COLOR_LATTICE);
    shellMat.emissiveIntensity = emissiveIntensity;
    shellMat.opacity = 0.85 + pulse * 0.1;

    latticeMat.opacity = 0.25 + activation * 0.35 + pulse * 0.4;
    auraMat.opacity = 0.06 + activation * 0.14 + pulse * 0.25;

    shell.rotation.y += 0.01 + pulse * 0.02;
    lattice.rotation.y -= 0.012;
    lattice.rotation.x += 0.008;
  });

  return (
    <GroupPrimitive position={[0, 1.05, -1]}>
      <mesh ref={shellRef} castShadow receiveShadow>
        <icosahedronGeometry args={[1, 2]} />
        <meshStandardMaterial color="#0f172a" metalness={0.6} roughness={0.2} transparent opacity={0.9} emissive="#0ea5e9" emissiveIntensity={0.4} />
      </mesh>
      <lineSegments ref={latticeRef} geometry={latticeGeometry}>
        <lineBasicMaterial color={COLOR_LATTICE} transparent opacity={0.45} linewidth={1} />
      </lineSegments>
      <mesh ref={auraRef} renderOrder={-1}>
        <sphereGeometry args={[1.4, 32, 32]} />
        <meshBasicMaterial color="#38bdf8" transparent opacity={0.1} />
      </mesh>
    </GroupPrimitive>
  );
}

function PhasePulse() {
  const ringRef = useRef<THREE.Mesh>(null!);

  useFrame(({ clock }) => {
    const info = getPhaseInfo(clock.getElapsedTime());
    const ring = ringRef.current;
    if (!ring) return;
    const mat = ring.material as THREE.MeshBasicMaterial;

    if (info.name === "pulse" || info.name === "execution") {
      const p = info.name === "pulse" ? info.progress : 1;
      const scale = THREE.MathUtils.lerp(1.2, 5.6, p);
      ring.visible = true;
      ring.scale.setScalar(scale);
      mat.opacity = THREE.MathUtils.lerp(0.35, 0, p);
    } else {
      ring.visible = false;
    }
  });

  return (
    <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]} position={[0, 1.05, -1]}>
      <ringGeometry args={[0.8, 0.85, 60]} />
      <meshBasicMaterial color="#38bdf8" transparent opacity={0.0} />
    </mesh>
  );
}

function PriceTrail() {
  const segments = 90;
  const positions = useMemo(() => {
    const arr = new Float32Array(segments * 3);
    for (let i = 0; i < segments; i++) {
      const x = (i / (segments - 1)) * 10 - 5;
      arr[i * 3 + 0] = x;
      arr[i * 3 + 1] = 1.2;
      arr[i * 3 + 2] = -1.8;
    }
    return arr;
  }, [segments]);

  const attrRef = useRef<THREE.BufferAttribute>(null);
  const lineRef = useRef<THREE.LineBasicMaterial>(null);

  useFrame(({ clock }) => {
    const attr = attrRef.current;
    if (!attr) return;
    const info = getPhaseInfo(clock.getElapsedTime());
    const t = clock.elapsedTime;
    const volatility = info.name === "pulse" ? 0.5 + info.progress * 0.6 : info.name === "execution" ? 1.2 : 0.4;

    for (let i = 0; i < attr.count; i++) {
      const x = attr.getX(i);
      const wave = Math.sin(x * 0.9 + t * 1.6) * 0.22 * volatility;
      const trend = Math.cos((x + t * 0.4) * 0.35) * 0.12;
      attr.setY(i, 1.05 + wave + trend);
    }
    attr.needsUpdate = true;

    if (lineRef.current) {
      const hueShift = info.name === "execution" ? THREE.MathUtils.lerp(0.53, 0.33, info.progress) : 0.53;
      lineRef.current.color.setHSL(hueShift, 0.85, 0.55 + Math.sin(t * 2) * 0.08);
    }
  });

  return (
    <GroupPrimitive position={[0, -0.05, -1.6]}>
      <line>
        <bufferGeometry>
          <bufferAttribute ref={attrRef as any} attach="attributes-position" array={positions} count={positions.length / 3} itemSize={3} />
        </bufferGeometry>
        <lineBasicMaterial ref={lineRef} color="#38bdf8" linewidth={1} />
      </line>
    </GroupPrimitive>
  );
}

type CandleDatum = {
  id: number;
  x: number;
  baseOpen: number;
  baseClose: number;
  baseHigh: number;
  baseLow: number;
};

function CandlestickField() {
  const data = useMemo<CandleDatum[]>(() => {
    const list: CandleDatum[] = [];
    let last = 0.3;
    for (let i = 0; i < 26; i++) {
      const open = last + THREE.MathUtils.randFloatSpread(0.25);
      const close = open + THREE.MathUtils.randFloatSpread(0.28);
      const high = Math.max(open, close) + Math.random() * 0.28;
      const low = Math.min(open, close) - Math.random() * 0.28;
      list.push({
        id: i,
        x: (i - 13) * 0.35,
        baseOpen: open,
        baseClose: close,
        baseHigh: high,
        baseLow: low,
      });
      last = close;
    }
    return list;
  }, []);

  const bodyRefs = useRef<(THREE.Mesh | null)[]>([]);
  const wickRefs = useRef<(THREE.Mesh | null)[]>([]);
  const wickGeometry = useMemo(() => new THREE.BoxGeometry(1, 1, 1), []);
  const bodyGeometry = useMemo(() => new THREE.BoxGeometry(1, 1, 1), []);

  useFrame(({ clock }) => {
    const info = getPhaseInfo(clock.getElapsedTime());
    const influence =
      info.name === "execution"
        ? THREE.MathUtils.smoothstep(info.progress, 0, 1)
        : info.name === "pulse"
        ? 0.4 + info.progress * 0.4
        : info.name === "core"
        ? info.progress * 0.3
        : 0;

    data.forEach((candle, idx) => {
      const body = bodyRefs.current[idx];
      const wick = wickRefs.current[idx];
      if (!body || !wick) return;

      const normalized = Math.abs(idx - data.length / 2) / (data.length / 2);
      const ripple = THREE.MathUtils.clamp(influence * 1.25 - normalized * 0.8 + 0.1, 0, 1);

      const targetHeight = THREE.MathUtils.lerp(Math.abs(candle.baseClose - candle.baseOpen), 0.7, ripple);
      const targetCenter = THREE.MathUtils.lerp((candle.baseOpen + candle.baseClose) / 2, candle.baseClose + 0.32, ripple);

      body.position.set(candle.x, targetCenter, -2.1);
      body.scale.set(0.22, Math.max(0.05, targetHeight), 0.22);

      const bodyMat = body.material as THREE.MeshStandardMaterial;
      const color = COLOR_NEGATIVE.clone().lerp(COLOR_POSITIVE, ripple);
      const emissive = COLOR_NEG_EMISSIVE.clone().lerp(COLOR_POS_EMISSIVE, ripple);
      bodyMat.color.copy(color);
      bodyMat.emissive.copy(emissive);
      bodyMat.emissiveIntensity = 0.18 + ripple * 0.6;

      const wickHeight = THREE.MathUtils.lerp(candle.baseHigh - candle.baseLow, 1, ripple);
      const wickCenter = THREE.MathUtils.lerp((candle.baseHigh + candle.baseLow) / 2, targetCenter + wickHeight * 0.4, ripple);
      wick.position.set(candle.x, wickCenter, -2.1);
      wick.scale.set(0.05, Math.max(0.12, wickHeight), 0.05);
    });
  });

  return (
    <GroupPrimitive position={[0, -1, 0]}>
      {data.map((candle, idx) => (
        <GroupPrimitive key={candle.id}>
          <mesh
            ref={(mesh) => {
              wickRefs.current[idx] = mesh;
            }}
            geometry={wickGeometry}
            scale={[0.05, candle.baseHigh - candle.baseLow, 0.05]}
            position={[candle.x, (candle.baseHigh + candle.baseLow) / 2, -2.1]}
          >
            <meshStandardMaterial color="#1e3a8a" emissive="#1d4ed8" emissiveIntensity={0.2} roughness={0.45} />
          </mesh>
          <mesh
            ref={(mesh) => {
              bodyRefs.current[idx] = mesh;
            }}
            geometry={bodyGeometry}
            scale={[0.22, Math.abs(candle.baseClose - candle.baseOpen), 0.22]}
            position={[candle.x, (candle.baseOpen + candle.baseClose) / 2, -2.1]}
          >
            <meshStandardMaterial color="#f87171" emissive="#7f1d1d" emissiveIntensity={0.18} metalness={0.35} roughness={0.25} />
          </mesh>
        </GroupPrimitive>
      ))}
    </GroupPrimitive>
  );
}

function ExecutionBeam() {
  const beamRef = useRef<THREE.Mesh>(null!);
  const glowRef = useRef<THREE.Mesh>(null!);

  useFrame(({ clock }) => {
    const info = getPhaseInfo(clock.getElapsedTime());
    const beam = beamRef.current;
    const glow = glowRef.current;
    if (!beam || !glow) return;

    const activation = info.name === "pulse" ? info.progress : info.name === "execution" ? 1 - THREE.MathUtils.lerp(0, 0.6, info.progress) : 0;
    const length = THREE.MathUtils.lerp(0.3, 9, activation);
    const radius = THREE.MathUtils.lerp(0.12, 0.3, activation);

    beam.visible = activation > 0.02;
    glow.visible = activation > 0.02;

    beam.scale.set(radius, length, radius);
    glow.scale.set(radius * 1.6, length * 1.05, radius * 1.6);

    beam.position.set(0, 1.05, -1 + length * 0.5);
    glow.position.set(0, 1.05, -1 + length * 0.5);

    const beamMat = beam.material as THREE.MeshStandardMaterial;
    beamMat.emissive = COLOR_BEAM;
    beamMat.emissiveIntensity = 1.2 + activation * 1.8;

    const glowMat = glow.material as THREE.MeshBasicMaterial;
    glowMat.opacity = 0.18 + activation * 0.35;
  });

  return (
    <GroupPrimitive rotation={[-Math.PI / 2, 0, 0]}>
      <mesh ref={beamRef} visible={false}>
        <cylinderGeometry args={[0.2, 0.2, 1, 24, 1, true]} />
        <meshStandardMaterial color="#fde68a" emissive="#facc15" emissiveIntensity={1.2} roughness={0.1} metalness={0.4} transparent opacity={0.95} />
      </mesh>
      <mesh ref={glowRef} visible={false}>
        <cylinderGeometry args={[0.25, 0.25, 1, 24, 1, true]} />
        <meshBasicMaterial color="#facc15" transparent opacity={0.2} />
      </mesh>
    </GroupPrimitive>
  );
}

function HeroTitle() {
  const textRef = useRef<any>(null!);
  useFrame(({ clock }) => {
    const info = getPhaseInfo(clock.getElapsedTime());
    const emphasis = info.name === "pulse" ? 0.6 + info.progress * 0.4 : info.name === "execution" ? 0.8 : 0.5;
    const mat = textRef.current?.material as THREE.MeshStandardMaterial | undefined;
    if (mat) {
      mat.emissiveIntensity = 0.25 + emphasis;
    }
    if (textRef.current) {
      const scale = 1 + Math.sin(clock.elapsedTime * 0.8) * 0.015 + emphasis * 0.05;
      textRef.current.scale.setScalar(scale);
    }
  });

  return (
    <Text ref={textRef} position={[0, 2.2, -1.4]} fontSize={0.8} letterSpacing={0.04} anchorX="center" anchorY="middle">
      ALPHINTRA
      <meshStandardMaterial color="#e2e8f0" emissive="#38bdf8" emissiveIntensity={0.6} roughness={0.3} metalness={0.4} transparent opacity={0.9} depthTest={false} />
    </Text>
  );
}

function randomPointInSphere(radius: number) {
  const u = Math.random();
  const v = Math.random();
  const theta = u * 2 * Math.PI;
  const phi = Math.acos(2 * v - 1);
  const r = radius * Math.cbrt(Math.random());
  return new THREE.Vector3(
    r * Math.sin(phi) * Math.cos(theta),
    r * Math.sin(phi) * Math.sin(theta),
    r * Math.cos(phi)
  );
}
