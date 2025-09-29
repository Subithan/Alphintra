"use client";

import React, { useMemo } from "react";

type LandingPreloaderProps = {
  progress: number;
  isReady: boolean;
};

export function LandingPreloader({ progress, isReady }: LandingPreloaderProps) {
  const clampedProgress = useMemo(() => {
    if (Number.isNaN(progress)) {
      return 0;
    }
    return Math.min(100, Math.max(0, progress));
  }, [progress]);

  return (
    <div
      className={`pointer-events-none fixed inset-0 z-30 flex items-center justify-center bg-slate-950/90 transition-opacity duration-700 ${
        isReady ? "opacity-0" : "opacity-100"
      }`}
      aria-hidden={isReady}
    >
      <div className="pointer-events-auto flex w-72 max-w-full flex-col items-center gap-6 rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur">
        <div className="text-center">
          <p className="text-xs uppercase tracking-[0.35em] text-white/60">Loading</p>
          <p className="mt-3 text-2xl font-semibold text-white">Preparing experience</p>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-emerald-400 transition-all duration-500"
            style={{ width: `${clampedProgress}%` }}
          />
        </div>
        <span className="text-sm font-medium text-white/80">{Math.round(clampedProgress)}%</span>
      </div>
    </div>
  );
}
