"use client";

import React, { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export default function StrategyPin() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const lineRef = useRef<HTMLDivElement>(null);
  const stepsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = sectionRef.current;
    const line = lineRef.current;
    const steps = stepsRef.current;
    if (!el || !line || !steps) return;

    const cards = steps.querySelectorAll<HTMLElement>(".step-card");
    const checks = steps.querySelectorAll<HTMLElement>(".step-check");

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: el,
          pin: true,
          start: "top top",
          end: "+=1400",
          scrub: 1,
        },
        defaults: { ease: "power2.out" },
      });

      // Intro fade
      tl.fromTo(
        ".strategy-title",
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.6 },
        0
      );

      // Animate cards in sequence with line growth and check toggles
      cards.forEach((card, i) => {
        const at = i * 0.6 + 0.3;
        tl.fromTo(
          card,
          { y: 40, opacity: 0, rotateX: -8 },
          { y: 0, opacity: 1, rotateX: 0, duration: 0.6 },
          at
        );
        tl.to(
          line,
          { width: `${((i + 1) / cards.length) * 100}%`, duration: 0.5 },
          at + 0.2
        );
        tl.fromTo(
          checks[i],
          { scale: 0.6, opacity: 0 },
          { scale: 1, opacity: 1, duration: 0.3 },
          at + 0.45
        );
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} className="relative py-28">
      <div className="container mx-auto px-4">
        <div className="glass-strong rounded-2xl p-8 md:p-10">
          <h3 className="strategy-title text-2xl md:text-3xl font-semibold text-white text-center mb-6">
            Build a Strategy in 5 Steps
          </h3>

          {/* Progress line */}
          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div ref={lineRef} className="h-full w-0 bg-gradient-to-r from-emerald-400 via-cyan-400 to-yellow-400" />
          </div>

          {/* Steps */}
          <div ref={stepsRef} className="mt-8 grid grid-cols-1 md:grid-cols-5 gap-4">
            <Step index={1} title="Market & Asset" desc="Pick exchange, pair, and timeframe" />
            <Step index={2} title="Signals" desc="Define entries & exits with indicators" />
            <Step index={3} title="Risk" desc="Position size, stop loss, take profit" />
            <Step index={4} title="Backtest" desc="Run simulation with result insights" />
            <Step index={5} title="Deploy" desc="Go live on your connected account" />
          </div>
        </div>
      </div>
    </section>
  );
}

function Step({ index, title, desc }: { index: number; title: string; desc: string }) {
  return (
    <div className="step-card relative flex flex-col items-start gap-2 rounded-xl p-4 border border-white/15 bg-white/5 backdrop-blur-md">
      <div className="flex items-center justify-between w-full">
        <span className="text-xs text-white/70">Step {index}</span>
        <span className="step-check inline-flex items-center justify-center text-emerald-400/90 text-lg">✓</span>
      </div>
      <div className="font-semibold text-white">{title}</div>
      <div className="text-xs text-white/70 leading-relaxed">{desc}</div>
    </div>
  );
}
