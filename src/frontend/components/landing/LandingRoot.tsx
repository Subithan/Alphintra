"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";

import { Navbar } from "./Navbar";
import { Hero } from "./Hero";
import { Features } from "./Features";
import { FAQ } from "./FAQ";
import { CallToAction } from "./CallToAction";
import { Footer } from "./Footer";
import PinSection from "../gsap/PinSection";
import StrategyPin from "../gsap/StrategyPin";
import { LandingPreloader } from "./LandingPreloader";

type CanvasComponentProps = {
  onProgress?: (progress: number) => void;
  onReady?: () => void;
};

type CanvasComponent = React.ComponentType<CanvasComponentProps>;

export default function LandingRoot() {
  const [Canvas3D, setCanvas3D] = useState<CanvasComponent | null>(null);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [isReady, setIsReady] = useState(false);
  const originalOverflowRef = useRef<string | null>(null);

  const handleProgress = useCallback((progress: number) => {
    setLoadingProgress(progress);
  }, []);

  const handleReady = useCallback(() => {
    setLoadingProgress(100);
    setIsReady(true);
  }, []);

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

  useEffect(() => {
    if (typeof document === "undefined") return;

    if (originalOverflowRef.current === null) {
      originalOverflowRef.current = document.body.style.overflow || "";
    }

    if (!isReady) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = originalOverflowRef.current;
    }

    return () => {
      document.body.style.overflow = originalOverflowRef.current ?? "";
    };
  }, [isReady]);

  return (
    <>
      <LandingPreloader progress={loadingProgress} isReady={isReady} />

      {/* 3D background canvas */}
      <div className="fixed inset-0 z-0">
        {Canvas3D ? (
          <Canvas3D onProgress={handleProgress} onReady={handleReady} />
        ) : null}
      </div>

      {/* Foreground content layered above 3D scene */}
      <div
        className={`relative z-10 transition-opacity duration-700 ${
          isReady ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"
        }`}
        aria-hidden={!isReady}
      >
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
