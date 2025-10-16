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
  const [displayProgress, setDisplayProgress] = useState(0);
  const [sceneReady, setSceneReady] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const originalOverflowRef = useRef<string | null>(null);
  const startTimeRef = useRef<number>(Date.now());
  const rafRef = useRef<number | null>(null);

  const MIN_PRELOADER_MS = 1200;

  const handleProgress = useCallback((progress: number) => {
    setLoadingProgress(progress);
  }, []);

  const handleReady = useCallback(() => {
    setLoadingProgress(100);
    setSceneReady(true);
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

  // Smooth progress driver and gating for minimal display time
  useEffect(() => {
    const tick = () => {
      const target = sceneReady ? 100 : Math.min(95, loadingProgress);
      const diff = target - displayProgress;
      let next = displayProgress;
      if (Math.abs(diff) > 0.01) {
        const step = Math.max(0.3, Math.abs(diff) * (sceneReady ? 0.18 : 0.12));
        next = displayProgress + Math.sign(diff) * step;
        if ((diff > 0 && next > target) || (diff < 0 && next < target)) next = target;
        setDisplayProgress(Number(next.toFixed(2)));
      }

      const elapsed = Date.now() - startTimeRef.current;
      if (!isReady && sceneReady && next >= 100 && elapsed >= MIN_PRELOADER_MS) {
        setIsReady(true);
      }

      if (!isReady) {
        rafRef.current = requestAnimationFrame(tick);
      } else if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };

    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    };
  }, [loadingProgress, sceneReady, isReady, displayProgress]);

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
      <LandingPreloader progress={displayProgress} isReady={isReady} />

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
