'use client';

import { useEffect, useMemo, useRef } from 'react';
import { gsap } from 'gsap';

type LandingPreloaderProps = {
  progress: number;
  isReady: boolean;
};

const clampProgress = (value: number) => Math.min(100, Math.max(0, value));

export function LandingPreloader({ progress, isReady }: LandingPreloaderProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const chartFillRef = useRef<SVGRectElement>(null);
  const percentageRef = useRef<HTMLSpanElement>(null);
  const percentageTween = useRef({ value: 0 });
  const completionTimeline = useRef<gsap.core.Timeline | null>(null);

  const normalizedProgress = useMemo(() => clampProgress(progress), [progress]);

  useEffect(() => {
    if (!overlayRef.current || !chartFillRef.current) {
      return;
    }

    const ctx = gsap.context(() => {
      gsap.set(chartFillRef.current, { scaleY: 0, transformOrigin: '50% 100%' });
      gsap.set(overlayRef.current, { autoAlpha: 1 });
    }, overlayRef);

    return () => ctx.revert();
  }, []);

  useEffect(() => {
    if (!chartFillRef.current) {
      return;
    }

    gsap.to(chartFillRef.current, {
      scaleY: normalizedProgress / 100,
      duration: 0.8,
      ease: 'power2.out',
    });
  }, [normalizedProgress]);

  useEffect(() => {
    if (!percentageRef.current) {
      return;
    }

    const target = percentageTween.current;

    gsap.to(target, {
      value: normalizedProgress,
      duration: 0.6,
      ease: 'power2.out',
      onUpdate: () => {
        if (percentageRef.current) {
          percentageRef.current.textContent = `${Math.round(target.value)}%`;
        }
      },
    });
  }, [normalizedProgress]);

  useEffect(() => {
    if (!overlayRef.current) {
      return;
    }

    if (isReady) {
      completionTimeline.current?.kill();
      completionTimeline.current = gsap.timeline();
      completionTimeline.current
        .to(chartFillRef.current, {
          duration: 0.5,
          scaleY: 1,
          ease: 'power3.out',
        })
        .to(
          overlayRef.current,
          {
            duration: 0.6,
            autoAlpha: 0,
            pointerEvents: 'none',
            ease: 'power2.out',
          },
          '-=0.2',
        );
    } else {
      completionTimeline.current?.kill();
      gsap.to(overlayRef.current, {
        duration: 0.3,
        autoAlpha: 1,
        pointerEvents: 'auto',
      });
    }
  }, [isReady]);

  useEffect(() => () => completionTimeline.current?.kill(), []);

  return (
    <div
      ref={overlayRef}
      role="status"
      aria-live="polite"
      aria-busy={!isReady}
      className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-primary/95 via-slate-950 to-slate-900 text-primary-foreground"
    >
      <div className="flex w-full max-w-xl flex-col items-center gap-10 px-6 py-10 text-center">
        <div className="rounded-3xl border border-white/20 bg-white/5 p-8 shadow-2xl backdrop-blur">
          <div className="mb-6 text-sm font-semibold uppercase tracking-[0.25em] text-primary-foreground/80">
            Preparing your trading intelligence
          </div>
          <div className="relative mx-auto flex h-64 w-64 items-center justify-center">
            <svg
              viewBox="0 0 220 220"
              role="img"
              aria-label={`Loading ${Math.round(normalizedProgress)} percent`}
              className="h-full w-full"
            >
              <defs>
                <linearGradient id="chart-fill" x1="0" x2="0" y1="1" y2="0">
                  <stop offset="0%" stopColor="hsl(var(--primary))" />
                  <stop offset="100%" stopColor="hsl(var(--accent))" />
                </linearGradient>
              </defs>
              <rect x="20" y="20" width="180" height="180" rx="28" className="fill-white/5 stroke-white/20" strokeWidth="4" />
              <rect
                ref={chartFillRef}
                x="20"
                y="20"
                width="180"
                height="180"
                rx="28"
                className="origin-bottom fill-[url(#chart-fill)] opacity-90"
              />
              <g transform="translate(20 20)">
                {[1, 2, 3, 4].map((index) => (
                  <line
                    key={`grid-${index}`}
                    x1="0"
                    x2="180"
                    y1={36 * index}
                    y2={36 * index}
                    className="stroke-white/15"
                    strokeWidth="2"
                  />
                ))}
              </g>
              <g transform="translate(20 20)" className="text-left">
                {[0, 25, 50, 75, 100].map((value) => (
                  <text
                    key={`label-${value}`}
                    x="190"
                    y={180 - (value / 100) * 180}
                    dy="6"
                    className="fill-white/60 text-[14px]"
                    textAnchor="start"
                  >
                    {value}%
                  </text>
                ))}
              </g>
            </svg>
          </div>
          <div className="flex flex-col items-center gap-2">
            <span ref={percentageRef} className="text-5xl font-bold tracking-tight text-white">
              0%
            </span>
            <span className="text-base text-white/70">Calibrating predictive indices…</span>
          </div>
        </div>
        <p className="max-w-md text-sm text-white/70">
          We&apos;re synchronizing your personalized analytics workspace to ensure real-time risk signals and
          market intelligence are ready the moment you arrive.
        </p>
      </div>
    </div>
  );
}

export default LandingPreloader;
