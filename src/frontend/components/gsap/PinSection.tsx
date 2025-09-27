"use client";

import React, { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

// Register plugin once in module scope (safe in client-only file)
gsap.registerPlugin(ScrollTrigger);

export default function PinSection() {
  const ref = useRef<HTMLDivElement>(null);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    const box = boxRef.current;
    if (!el || !box) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: el,
          pin: true,
          start: "top top",
          end: "+=800",
          scrub: 1,
        },
      });
      tl.to(box, { rotate: 360, xPercent: 120, duration: 1 })
        .to(box, { backgroundColor: "#f59e0b", duration: 0.5 })
        .to(box, { rotate: 0, xPercent: 0, duration: 1 });
    }, ref);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={ref} className="relative py-32">
      <div className="container mx-auto px-4">
        <div className="glass-strong rounded-2xl p-10 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Immersive Scroll Story</h2>
          <p className="text-gray-300 mb-10">
            This section pins to the viewport and scrubs an animation timeline as you scroll.
          </p>
          <div
            ref={boxRef}
            className="w-32 h-32 bg-yellow-400 rounded-xl mx-auto will-change-transform"
          />
        </div>
      </div>
    </section>
  );
}
