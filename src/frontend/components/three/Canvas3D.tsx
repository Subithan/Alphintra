"use client";

import React, { Suspense, useEffect, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { Preload, useProgress } from "@react-three/drei";
import Scene from "./Scene";

type Canvas3DProps = {
  onProgress?: (progress: number) => void;
  onReady?: () => void;
};

export default function Canvas3D({ onProgress, onReady }: Canvas3DProps) {
  const progress = useProgress();
  const hasNotifiedReadyRef = useRef(false);

  useEffect(() => {
    if (onProgress) {
      onProgress(progress.progress);
    }
  }, [onProgress, progress.progress]);

  useEffect(() => {
    if (!progress.active && progress.progress === 100) {
      if (!hasNotifiedReadyRef.current) {
        hasNotifiedReadyRef.current = true;
        onReady?.();
      }
    } else {
      hasNotifiedReadyRef.current = false;
    }
  }, [onReady, progress.active, progress.progress]);

function ProgressBridge({ onProgress, onReady }: Canvas3DProps) {
  const { progress, active } = useProgress();
  const readyEmittedRef = useRef(false);

  useEffect(() => {
    if (onProgress) {
      onProgress(progress);
    }
  }, [progress, onProgress]);

  useEffect(() => {
    if (!active && !readyEmittedRef.current) {
      readyEmittedRef.current = true;
      onReady?.();
    }
  }, [active, onReady]);

  return null;
}

export default function Canvas3D({ onProgress, onReady }: Canvas3DProps) {
  return (
    <Canvas
      gl={{ antialias: true, powerPreference: "high-performance" }}
      dpr={[1, 2]}
      camera={{ fov: 60, near: 0.1, far: 100, position: [0, 1.2, 6] }}
      shadows={false}
      frameloop="always"
    >
      <Suspense fallback={<CanvasFallback />}>
        <Scene />
        <Preload all />
        <ProgressBridge onProgress={onProgress} onReady={onReady} />
      </Suspense>
    </Canvas>
  );
}

function CanvasFallback() {
  return (
    <group>
      <color attach="background" args={["#050505"]} />
    </group>
  );
}
