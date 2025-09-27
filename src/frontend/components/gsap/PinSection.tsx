"use client";

import React, { useEffect, useMemo, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

// Register plugin once in module scope (safe in client-only file)
gsap.registerPlugin(ScrollTrigger);

export default function PinSection() {
  const ref = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const coreRef = useRef<HTMLDivElement>(null);
  const beamRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const captionsRef = useRef<HTMLDivElement>(null);

  const chipsCount = 28;
  const candlesCount = 24;
  const tickers = useMemo(
    () => [
      "BTC/USD",
      "ETH",
      "AAPL",
      "TSLA",
      "SOL",
      "ADA",
      "EURUSD",
      "XAU",
      "SPY",
      "NIFTY50",
    ],
    []
  );

  useEffect(() => {
    const el = ref.current;
    const stage = stageRef.current;
    const core = coreRef.current;
    const beam = beamRef.current;
    if (!el || !stage || !core || !beam) return;

    const ctx = gsap.context(() => {
      // Randomize chip start positions (CSS vars)
      const chipNodes = Array.from(stage.querySelectorAll<HTMLSpanElement>(".pin-chip"));
      const { width, height } = stage.getBoundingClientRect();
      chipNodes.forEach((chip) => {
        const angle = Math.random() * Math.PI * 2;
        const radius = Math.max(width, height) * (0.6 + Math.random() * 0.7);
        const tx = Math.cos(angle) * radius;
        const ty = Math.sin(angle) * radius;
        chip.style.setProperty("--tx", `${tx}px`);
        chip.style.setProperty("--ty", `${ty}px`);
        chip.style.opacity = "0";
        chip.style.transform = `translate(${tx}px, ${ty}px) scale(0.6)`;
      });

      // Candlesticks initial red state is in CSS; we flip to green later
      const bodies = stage.querySelectorAll<HTMLElement>(".pin-candle-body");
      const wicks = stage.querySelectorAll<HTMLElement>(".pin-candle-wick");

      // Main scroll-driven timeline
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: el,
          pin: true,
          start: "top top",
          end: "+=1600",
          scrub: 1,
        },
        defaults: { ease: "power2.out" },
      });

      // Update progress bar on timeline updates (avoid relying on self argument)
      tl.eventCallback("onUpdate", () => {
        const p = progressRef.current;
        if (p) {
          const percent = tl.progress() * 100;
          gsap.to(p, { width: `${percent}%`, overwrite: true, duration: 0.1 });
        }
      });

      // Collect captions
      const captions = Array.from((captionsRef.current as HTMLDivElement).querySelectorAll<HTMLElement>(".pin-caption"));
      gsap.set(captions, { opacity: 0, y: 8 });

      // Phase 1: Data influx — chips converge
      tl.to(
        chipNodes,
        {
          x: 0,
          y: 0,
          scale: 1,
          opacity: 1,
          stagger: { each: 0.02, from: "random" },
          duration: 1.2,
        },
        0
      );
      tl.to(captions[0], { opacity: 1, y: 0, duration: 0.45 }, 0)
        .to(captions[0], { opacity: 0, y: -6, duration: 0.45 }, 0.9);

      // Phase 2: Neural core awakens — glow + pulse ring
      tl.to(
        core,
        {
          scale: 1.15,
          boxShadow:
            "0 0 80px rgba(56,189,248,0.45), inset 0 0 40px rgba(56,189,248,0.6)",
          duration: 0.9,
        },
        ">-0.4"
      ).fromTo(
        stage.querySelector(".pin-pulse") as HTMLElement,
        { scale: 1, opacity: 0.35 },
        { scale: 6, opacity: 0, duration: 0.9 },
        "<"
      ).to(captions[1], { opacity: 1, y: 0, duration: 0.45 }, ">-0.2")
        .to(captions[1], { opacity: 0, y: -6, duration: 0.45 }, ">0.6");

      // Phase 3: Execution — beam fires + candles flip green
      tl.fromTo(
        beam,
        { scaleX: 0, opacity: 0 },
        { scaleX: 1, opacity: 1, duration: 0.7, ease: "power3.out" },
        ">-0.2"
      ).to(
        bodies,
        {
          backgroundColor: "#22c55e",
          borderColor: "#16a34a",
          boxShadow: "0 0 12px rgba(34,197,94,0.45)",
          stagger: 0.03,
          duration: 0.6,
        },
        "<"
      ).to(
        wicks,
        { backgroundColor: "#1d4ed8", borderColor: "#1d4ed8", duration: 0.6 },
        "<"
      ).to(captions[2], { opacity: 1, y: 0, duration: 0.45 }, ">-0.2")
        .to(captions[2], { opacity: 0, y: -6, duration: 0.45 }, ">0.8");
    }, ref);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={ref} className="relative py-32">
      <div className="container mx-auto px-4">
        <div className="glass-strong rounded-2xl p-8 md:p-10 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-2">
            Immersive Scroll Story
          </h2>
          <p className="text-gray-300 mb-6">
            Scroll to watch data converge, the Alphintra core awaken, and a decisive execution ripple through the market.
          </p>

          {/* Stage */}
          <div
            ref={stageRef}
            className="relative mx-auto mt-2 h-[56vh] md:h-[50vh] overflow-hidden rounded-xl border border-white/10 bg-black/40 backdrop-blur-md"
          >
            {/* Captions */}
            <div
              ref={captionsRef}
              className="absolute top-4 left-1/2 -translate-x-1/2 z-10 pointer-events-none space-y-1"
            >
              <div className="pin-caption text-white/90 text-sm md:text-base">
                Data streams converge to the core
              </div>
              <div className="pin-caption text-white/90 text-sm md:text-base">
                Alphintra Core awakens
              </div>
              <div className="pin-caption text-white/90 text-sm md:text-base">
                Execution signal flips the market
              </div>
            </div>
            {/* Converging data chips */}
            <div className="absolute inset-0 pointer-events-none">
              {Array.from({ length: chipsCount }).map((_, i) => (
                <span
                  key={i}
                  className="pin-chip absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-[10px] md:text-xs px-2 py-1 rounded-full border border-white/15 bg-white/10 backdrop-blur-sm text-white/90 shadow-sm"
                  style={{
                    // randomized via JS in useEffect with CSS vars --tx, --ty
                  }}
                >
                  {tickers[i % tickers.length]}
                </span>
              ))}
            </div>

            {/* Core orb + pulse */}
            <div
              ref={coreRef}
              className="pin-orb absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
            />
            <div className="pin-pulse absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" />

            {/* Execution beam */}
            <div
              ref={beamRef}
              className="pin-beam absolute left-1/2 top-1/2 -translate-y-1/2 origin-left"
            />

            {/* Candlestick strip */}
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-end gap-2">
              {Array.from({ length: candlesCount }).map((_, i) => {
                const h = 16 + Math.round(Math.random() * 48);
                const wick = h + 20 + Math.round(Math.random() * 16);
                return (
                  <div key={i} className="flex flex-col items-center">
                    <div
                      className="pin-candle-wick"
                      style={{ height: wick }}
                    />
                    <div
                      className="pin-candle-body"
                      style={{ height: h }}
                    />
                  </div>
                );
              })}
            </div>

            {/* Progress bar */}
            <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-white/10">
              <div ref={progressRef} className="h-full w-0 bg-gradient-to-r from-cyan-400 via-emerald-400 to-yellow-400" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
