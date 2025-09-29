"use client";

import React, { useEffect, useState } from "react";

import { Navbar } from "./Navbar";
import { Hero } from "./Hero";
import { Features } from "./Features";
import { FAQ } from "./FAQ";
import { CallToAction } from "./CallToAction";
import { Footer } from "./Footer";
import PinSection from "../gsap/PinSection";
import StrategyPin from "../gsap/StrategyPin";
import { useLandingAssetLoader } from "@/hooks/useLandingAssetLoader";
import { LandingPreloader } from "./LandingPreloader";

type CanvasComponent = React.ComponentType<Record<string, unknown>>;

export default function LandingRoot() {
  const { Canvas3D, ready, progress } = useLandingAssetLoader();

  return (
    <>
      <LandingPreloader progress={progress} ready={!!ready} />

      {/* 3D background canvas */}
      <div className={`fixed inset-0 z-0 transition-opacity duration-700 ease-out ${ready ? "opacity-100" : "opacity-0"}`}>
        {Canvas3D ? <Canvas3D /> : null}
      </div>

      {/* Foreground content layered above 3D scene */}
      <div className={`relative z-10 transition-opacity duration-500 ease-out ${ready ? "opacity-100" : "pointer-events-none select-none opacity-0"}`}>
        <Navbar />
        <Hero />
        {/* Pinned scroll storytelling section */}
        <PinSection />
        <StrategyPin />
        <Features />
        <FAQ />
        <CallToAction />
        <Footer />
      </div>
    </>
  );
}
