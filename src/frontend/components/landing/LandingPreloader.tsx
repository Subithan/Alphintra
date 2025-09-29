"use client";

import React, { useEffect, useMemo, useState } from "react";

type LandingPreloaderProps = {
  progress: number;
  ready: boolean;
};

export function LandingPreloader({ progress, ready }: LandingPreloaderProps) {
  const [visible, setVisible] = useState(true);
  const [reduceMotion, setReduceMotion] = useState(false);

  const clamped = useMemo(
    () => Math.max(0, Math.min(100, Math.round(progress))),
    [progress]
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduceMotion(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (!ready) return;
    const timeout = window.setTimeout(() => setVisible(false), 600);
    return () => window.clearTimeout(timeout);
  }, [ready]);

  if (!visible) return null;

  const chartHeight = 160;
  const fillHeight = (clamped / 100) * chartHeight;
  const fillY = 190 - fillHeight;

  return (
    <div
      className={`fixed inset-0 z-40 flex items-center justify-center bg-[#05070c] transition-opacity duration-500 ${
        ready ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
      role="status"
      aria-live="polite"
      aria-label={`Loading trading environment ${clamped}%`}
    >
      <div className="flex flex-col items-center gap-8 text-white">
        <div className="relative h-[220px] w-[300px]">
          <svg viewBox="0 0 320 220" className="h-full w-full">
            <defs>
              <clipPath id="chart-fill-clip">
                <path d="M40 30 L40 190 L280 190 L280 70 L240 90 L210 75 L170 110 L140 85 L100 140 L70 120 L70 30 Z" />
              </clipPath>
              <linearGradient id="fill-gradient" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#3CF5A3" />
                <stop offset="100%" stopColor="#0B8043" />
              </linearGradient>
            </defs>

            <rect
              x="40"
              y="30"
              width="240"
              height="160"
              rx="12"
              fill="none"
              stroke="rgba(255,255,255,0.25)"
              strokeWidth="2"
            />

            <g stroke="rgba(255,255,255,0.08)" strokeWidth="1">
              {[0, 1, 2, 3].map((line) => (
                <line
                  key={`h-${line}`}
                  x1="40"
                  x2="280"
                  y1={70 + line * 30}
                  y2={70 + line * 30}
                  strokeDasharray="4 8"
                />
              ))}
              {[0, 1, 2, 3, 4].map((line) => (
                <line
                  key={`v-${line}`}
                  x1={80 + line * 40}
                  x2={80 + line * 40}
                  y1="30"
                  y2="190"
                  strokeDasharray="4 8"
                />
              ))}
            </g>

            <g clipPath="url(#chart-fill-clip)">
              <rect
                x="40"
                y={fillY}
                width="240"
                height={fillHeight}
                fill="url(#fill-gradient)"
              />
              <g
                className={!reduceMotion ? "wave wave--one" : undefined}
                transform={`translate(0 ${fillY - 12})`}
              >
                <path
                  d="M0 24 C20 10 40 10 60 24 S100 38 120 24 160 10 180 24 220 38 240 24 280 10 300 24 340 38 360 24 V60 H0 Z"
                  fill="rgba(60, 245, 163, 0.35)"
                />
              </g>
              <g
                className={!reduceMotion ? "wave wave--two" : undefined}
                transform={`translate(-40 ${fillY - 18})`}
              >
                <path
                  d="M0 30 C30 16 60 16 90 30 S150 44 180 30 240 16 270 30 330 44 360 30 V70 H0 Z"
                  fill="rgba(15, 128, 67, 0.25)"
                />
              </g>
            </g>

            <polyline
              points="40,170 70,120 100,140 140,85 170,110 210,75 240,90 280,70"
              fill="none"
              stroke="#7FFFD4"
              strokeWidth="4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <circle cx="280" cy="70" r="6" fill="#7FFFD4" />

            <text
              x="40"
              y="210"
              fill="rgba(255,255,255,0.6)"
              fontSize="12"
              letterSpacing="3"
            >
              ALPHINTRA MARKETS
            </text>
          </svg>
        </div>

        <div className="text-center">
          <p className="text-sm uppercase tracking-[0.4em] text-white/50">
            Loading Trading Environment
          </p>
          <p className="mt-3 font-mono text-4xl tabular-nums">{clamped}%</p>
        </div>
      </div>

      <style jsx>{`
        .wave {
          animation: waveMove 6s linear infinite;
          will-change: transform;
        }
        .wave--two {
          animation-duration: 8s;
          animation-direction: reverse;
        }
        @keyframes waveMove {
          0% { transform: translateX(0); }
          100% { transform: translateX(-80px); }
        }
      `}</style>
    </div>
  );
}

