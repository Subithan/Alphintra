'use client';

import { useCallback, useEffect, useMemo, useRef } from 'react';
import { gsap } from 'gsap';

type LandingPreloaderProps = {
  progress: number;
  isReady: boolean;
};

const clampProgress = (value: number) => Math.min(100, Math.max(0, value));
const FILL_HEIGHT = 200;

export function LandingPreloader({ progress, isReady }: LandingPreloaderProps) {
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const percentageRef = useRef<HTMLSpanElement | null>(null);
  const percentageTween = useRef({ value: 0 });
  const waterContainerRef = useRef<SVGGElement | null>(null);
  const waterLevelRef = useRef<SVGGElement | null>(null);
  const waveRefs = useRef<(SVGPathElement | null)[]>([]);
  const sparklesRef = useRef<SVGGElement | null>(null);
  const completionTimeline = useRef<gsap.core.Timeline | null>(null);

  const normalizedProgress = useMemo(() => clampProgress(progress), [progress]);

  const setWaveRef = useCallback((index: number) => (node: SVGPathElement | null) => {
    waveRefs.current[index] = node;
  }, []);

  useEffect(() => {
    if (!overlayRef.current) {
      return;
    }

    const ctx = gsap.context(() => {
      gsap.set(overlayRef.current, { autoAlpha: 1 });

      if (waterLevelRef.current) {
        gsap.set(waterLevelRef.current, { y: FILL_HEIGHT });
      }

      if (sparklesRef.current) {
        gsap.set(sparklesRef.current, { autoAlpha: 0, scale: 0.85, transformOrigin: '50% 50%' });
      }

      if (waterContainerRef.current) {
        gsap.to(waterContainerRef.current, {
          duration: 6,
          y: '+=8',
          ease: 'sine.inOut',
          repeat: -1,
          yoyo: true,
        });
      }

      waveRefs.current.forEach((wave, index) => {
        if (!wave) {
          return;
        }

        const direction = index % 2 === 0 ? -1 : 1;
        gsap.set(wave, {
          transformOrigin: '50% 50%',
          xPercent: direction * 10,
        });

        gsap.to(wave, {
          duration: 5.5 + index * 0.8,
          xPercent: direction * 35,
          y: index === 0 ? -10 : -6,
          ease: 'sine.inOut',
          repeat: -1,
          yoyo: true,
        });
      });
    }, overlayRef);

    return () => ctx.revert();
  }, []);

  useEffect(() => {
    if (!waterLevelRef.current) {
      return;
    }

    const targetY = FILL_HEIGHT - (normalizedProgress / 100) * FILL_HEIGHT;

    gsap.to(waterLevelRef.current, {
      y: targetY,
      duration: 1.1,
      ease: 'power3.out',
    });
  }, [normalizedProgress]);

  useEffect(() => {
    if (!percentageRef.current) {
      return;
    }

    const target = percentageTween.current;

    gsap.to(target, {
      value: normalizedProgress,
      duration: 0.8,
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

      if (waterLevelRef.current) {
        completionTimeline.current.to(waterLevelRef.current, {
          duration: 0.8,
          y: 0,
          ease: 'power3.out',
        });
      }

      if (sparklesRef.current) {
        completionTimeline.current.to(
          sparklesRef.current,
          {
            duration: 0.6,
            autoAlpha: 1,
            scale: 1,
            ease: 'power2.out',
          },
          '-=0.4',
        );
      }

      completionTimeline.current.to(
        overlayRef.current,
        {
          duration: 0.7,
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

      if (sparklesRef.current) {
        gsap.set(sparklesRef.current, { autoAlpha: 0, scale: 0.85 });
      }
    }
  }, [isReady]);

  useEffect(() => () => completionTimeline.current?.kill(), []);

  return (
    <div
      ref={overlayRef}
      role="status"
      aria-live="polite"
      aria-busy={!isReady}
      className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-primary-foreground"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(56,189,248,0.18),transparent_55%)]" />
      <div className="relative flex w-full max-w-3xl flex-col items-center gap-12 px-6 py-10 text-center">
        <div className="relative w-full max-w-2xl overflow-hidden rounded-[2.5rem] border border-cyan-200/20 bg-white/5 p-10 shadow-[0_40px_120px_rgba(15,118,110,0.35)] backdrop-blur">
          <div className="mb-8 text-sm font-semibold uppercase tracking-[0.4em] text-cyan-100/80">
            Synchronizing market cockpit
          </div>
          <div className="relative mx-auto flex h-72 w-full max-w-xl items-center justify-center">
            <svg
              viewBox="0 0 260 260"
              role="img"
              aria-label={`Loading ${Math.round(normalizedProgress)} percent`}
              className="h-full w-full"
            >
              <defs>
                <linearGradient id="chart-frame" x1="0" x2="1" y1="1" y2="0">
                  <stop offset="0%" stopColor="rgba(15, 118, 110, 0.9)" />
                  <stop offset="50%" stopColor="rgba(56, 189, 248, 0.9)" />
                  <stop offset="100%" stopColor="rgba(59, 130, 246, 0.9)" />
                </linearGradient>
                <linearGradient id="water-fill" x1="0" x2="0" y1="1" y2="0">
                  <stop offset="0%" stopColor="rgba(16, 185, 129, 0.95)" />
                  <stop offset="35%" stopColor="rgba(45, 212, 191, 0.98)" />
                  <stop offset="75%" stopColor="rgba(56, 189, 248, 0.95)" />
                  <stop offset="100%" stopColor="rgba(165, 243, 252, 0.95)" />
                </linearGradient>
                <linearGradient id="water-shine" x1="0" x2="1" y1="0" y2="1">
                  <stop offset="0%" stopColor="rgba(255,255,255,0.7)" />
                  <stop offset="35%" stopColor="rgba(255,255,255,0.15)" />
                  <stop offset="100%" stopColor="rgba(255,255,255,0)" />
                </linearGradient>
                <radialGradient id="water-depth" cx="50%" cy="35%" r="75%">
                  <stop offset="0%" stopColor="rgba(255,255,255,0.55)" />
                  <stop offset="55%" stopColor="rgba(45,212,191,0.4)" />
                  <stop offset="100%" stopColor="rgba(12,74,110,0.65)" />
                </radialGradient>
                <radialGradient id="water-caustics" cx="50%" cy="20%" r="60%">
                  <stop offset="0%" stopColor="rgba(255,255,255,0.45)" />
                  <stop offset="65%" stopColor="rgba(191,235,255,0.12)" />
                  <stop offset="100%" stopColor="rgba(59,130,246,0)" />
                </radialGradient>
                <clipPath id="chart-mask">
                  <rect x="30" y="30" width="200" height="200" rx="34" ry="34" />
                </clipPath>
                <filter id="water-glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>
              <rect
                x="20"
                y="20"
                width="220"
                height="220"
                rx="40"
                className="fill-slate-900/60"
                stroke="url(#chart-frame)"
                strokeWidth="5"
              />
              <g clipPath="url(#chart-mask)">
                <g ref={waterContainerRef}>
                  <g ref={waterLevelRef}>
                    <rect
                      x="30"
                      y="30"
                      width="200"
                      height="200"
                      fill="url(#water-depth)"
                      filter="url(#water-glow)"
                    />
                    <path
                      ref={setWaveRef(0)}
                      d="M30 190 Q 60 175 90 190 T 150 190 T 210 190 L 230 230 L 30 230 Z"
                      fill="url(#water-fill)"
                      opacity="0.88"
                    />
                    <path
                      ref={setWaveRef(1)}
                      d="M30 200 Q 70 185 110 200 T 190 200 T 230 200 L 230 230 L 30 230 Z"
                      fill="url(#water-shine)"
                      opacity="0.75"
                    />
                    <ellipse
                      cx="130"
                      cy="170"
                      rx="95"
                      ry="28"
                      fill="url(#water-caustics)"
                      opacity="0.7"
                    />
                  </g>
                </g>
                <path
                  d="M30 65 C 110 18 150 18 230 62 L 230 30 L 30 30 Z"
                  fill="rgba(255,255,255,0.08)"
                />
                <rect x="30" y="200" width="200" height="30" fill="rgba(2,6,23,0.35)" />
                <g className="opacity-40">
                  {[0, 1, 2, 3, 4].map((index) => (
                    <line
                      key={`grid-${index}`}
                      x1="30"
                      x2="230"
                      y1={30 + (index * FILL_HEIGHT) / 4}
                      y2={30 + (index * FILL_HEIGHT) / 4}
                      stroke="rgba(148, 163, 184, 0.18)"
                      strokeWidth="1.5"
                    />
                  ))}
                  {[0, 1, 2, 3, 4, 5].map((index) => (
                    <line
                      key={`grid-vertical-${index}`}
                      x1={30 + (index * 200) / 5}
                      x2={30 + (index * 200) / 5}
                      y1="30"
                      y2="230"
                      stroke="rgba(148, 163, 184, 0.12)"
                      strokeWidth="1"
                    />
                  ))}
                </g>
                <g className="opacity-90">
                  {[40, 70, 110, 150, 190].map((x, idx) => (
                    <g key={`candle-${x}`}>
                      <line
                        x1={x + idx * 12}
                        x2={x + idx * 12}
                        y1={90 - (idx % 2 === 0 ? 20 : 10)}
                        y2={210 + (idx % 2 === 0 ? 10 : 18)}
                        stroke="rgba(56, 189, 248, 0.4)"
                        strokeWidth="3"
                      />
                      <rect
                        x={x - 6 + idx * 12}
                        y={idx % 2 === 0 ? 110 : 140}
                        width="18"
                        height={idx % 2 === 0 ? 70 : 50}
                        rx="4"
                        fill={idx % 2 === 0 ? 'rgba(74, 222, 128, 0.65)' : 'rgba(59, 130, 246, 0.5)'}
                      />
                    </g>
                  ))}
                </g>
              </g>
              <g ref={sparklesRef} className="pointer-events-none">
                {[0, 1, 2].map((index) => (
                  <circle
                    key={`sparkle-${index}`}
                    cx={90 + index * 50}
                    cy={70 + (index % 2 === 0 ? 0 : 20)}
                    r="6"
                    fill="rgba(224, 242, 254, 0.95)"
                  />
                ))}
              </g>
              <text x="130" y="258" textAnchor="middle" className="fill-cyan-100 text-[14px] tracking-[0.4em] uppercase">
                Liquidity rising
              </text>
            </svg>
          </div>
          <div className="flex flex-col items-center gap-3">
            <span ref={percentageRef} className="text-6xl font-black tracking-tight text-white">
              0%
            </span>
            <span className="text-base text-cyan-100/70">Priming alpha streams for launch…</span>
          </div>
        </div>
        <p className="max-w-2xl text-sm text-cyan-100/70">
          Our engines are hydrating your strategy dashboard with live liquidity flows, volatility clusters, and
          predictive signal overlays so you arrive to a fully-charged trading command center.
        </p>
      </div>
    </div>
  );
}

export default LandingPreloader;
