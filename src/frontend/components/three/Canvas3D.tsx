"use client";

import React, { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { Preload } from "@react-three/drei";
import Scene from "./Scene";

export default function Canvas3D() {
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
      </Suspense>
    </Canvas>
  );
}
