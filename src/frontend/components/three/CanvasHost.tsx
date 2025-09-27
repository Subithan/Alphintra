"use client";

import React from "react";
import dynamic from "next/dynamic";

// Dynamically import Canvas3D on the client only
const Canvas3D = dynamic(() => import("./Canvas3D"), { ssr: false });

export default function CanvasHost() {
  return <Canvas3D />;
}
