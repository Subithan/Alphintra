"use client";

import React, { Suspense, useEffect, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { Preload, useProgress } from "@react-three/drei";
import Scene from "./Scene";

type Canvas3DProps = {
  onProgress?: (progress: number) => void;
  onReady?: () => void;
};

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
      <Suspense fallback={null}>
        <Scene />
        <Preload all />
        <ProgressBridge onProgress={onProgress} onReady={onReady} />
      </Suspense>
    </Canvas>
  );
}
