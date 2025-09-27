"use client";

import React, { useEffect, useState } from "react";

import { Navbar } from "./Navbar";
import { Hero } from "./Hero";
import { Features } from "./Features";
import { FAQ } from "./FAQ";
import { CallToAction } from "./CallToAction";
import { Footer } from "./Footer";
import PinSection from "../gsap/PinSection";

type CanvasComponent = React.ComponentType<Record<string, unknown>>;

export default function LandingRoot() {
  const [Canvas3D, setCanvas3D] = useState<CanvasComponent | null>(null);

  useEffect(() => {
    let mounted = true;
    import("../three/Canvas3D").then((mod) => {
      if (mounted) {
        setCanvas3D(() => mod.default);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <>
      {/* 3D background canvas */}
      <div className="fixed inset-0 z-0">
        {Canvas3D ? <Canvas3D /> : null}
      </div>

      {/* Foreground content layered above 3D scene */}
      <div className="relative z-10">
        <Navbar />
        <Hero />
        {/* Pinned scroll storytelling section */}
        <PinSection />
        <Features />
        <FAQ />
        <CallToAction />
        <Footer />
      </div>
    </>
  );
}
