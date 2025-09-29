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
  const chartFillRef = useRef<SVGGElement>(null);
  const waveBobRef = useRef<SVGGElement>(null);
  const wavePrimaryRef = useRef<SVGPathElement>(null);
  const waveSecondaryRef = useRef<SVGPathElement>(null);
  const percentageRef = useRef<HTMLSpanElement>(null);
  const percentageTween = useRef({ value: 0 });
  const completionTimeline = useRef<gsap.core.Timeline | null>(null);

  const normalizedProgress = useMemo(() => clampProgress(progress), [progress]);

  useEffect(() => {
    if (!overlayRef.current || !chartFillRef.current) {
      return;
    }

    const ctx = gsap.context(() => {
      const restingLevel = 188;
      gsap.set(chartFillRef.current, { y: restingLevel });
      gsap.set(waveBobRef.current, { y: 0 });
      gsap.set(overlayRef.current, { autoAlpha: 1 });

      if (waveBobRef.current) {
        gsap.to(waveBobRef.current, {
          y: '-=6',
          duration: 2.8,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
        });
      }

      if (wavePrimaryRef.current) {
        gsap.to(wavePrimaryRef.current, {
          xPercent: -50,
          duration: 6.5,
          repeat: -1,
          ease: 'none',
        });
      }

      if (waveSecondaryRef.current) {
        gsap.to(waveSecondaryRef.current, {
          xPercent: -60,
          duration: 8,
          repeat: -1,
          ease: 'none',
        });
      }
    }, overlayRef);

    return () => ctx.revert();
  }, []);

  useEffect(() => {
    if (!chartFillRef.current) {
      return;
    }

    const minLevel = 82;
    const maxLevel = 188;
    const targetLevel = maxLevel - (normalizedProgress / 100) * (maxLevel - minLevel);

    gsap.to(chartFillRef.current, {
      y: targetLevel,
      duration: 1,
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
          duration: 0.6,
          y: 82,
          ease: 'power3.out',
        })
        .to(
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
    }
  }, [isReady]);

  useEffect(() => () => completionTimeline.current?.kill(), []);

  return (
    <div
      ref={overlayRef}
      role="status"
      aria-live="polite"
      aria-busy={!isReady}
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950 text-primary-foreground"
    >
      <div className="relative flex w-full max-w-4xl flex-col items-center gap-12 px-6 py-12 text-center">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.25),transparent_60%),radial-gradient(circle_at_80%_30%,rgba(16,185,129,0.28),transparent_65%)]" />
        <div className="relative rounded-[36px] border border-white/10 bg-white/[0.06] p-10 shadow-[0_40px_120px_rgba(15,118,110,0.35)] backdrop-blur-xl">
          <div className="mb-8 text-xs font-semibold uppercase tracking-[0.4em] text-white/70">
            Preparing your trading intelligence
          </div>
          <div className="relative mx-auto flex h-[18rem] w-[22rem] items-center justify-center">
            <svg
              viewBox="0 0 260 240"
              role="img"
              aria-label={`Loading ${Math.round(normalizedProgress)} percent`}
              className="h-full w-full"
            >
              <defs>
                <linearGradient id="chart-body" x1="0" x2="1" y1="0" y2="1">
                  <stop offset="0%" stopColor="rgba(148,163,184,0.45)" />
                  <stop offset="100%" stopColor="rgba(15,23,42,0.9)" />
                </linearGradient>
                <linearGradient id="chart-rim" x1="0" x2="1" y1="0" y2="1">
                  <stop offset="0%" stopColor="rgba(255,255,255,0.35)" />
                  <stop offset="100%" stopColor="rgba(16,185,129,0.25)" />
                </linearGradient>
                <linearGradient id="liquid-gradient" x1="0" x2="0" y1="1" y2="0">
                  <stop offset="0%" stopColor="rgba(16,185,129,0.95)" />
                  <stop offset="45%" stopColor="rgba(45,212,191,0.9)" />
                  <stop offset="100%" stopColor="rgba(125,249,255,0.75)" />
                </linearGradient>
                <radialGradient id="liquid-highlight" cx="30%" cy="20%" r="70%">
                  <stop offset="0%" stopColor="rgba(255,255,255,0.65)" />
                  <stop offset="70%" stopColor="rgba(255,255,255,0)" />
                </radialGradient>
                <clipPath id="liquid-clip">
                  <path d="M46 74 L184 58 L214 84 V194 L176 214 L42 198 L30 182 V96 Z" />
                </clipPath>
                <filter id="inner-glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur in="SourceAlpha" stdDeviation="6" result="blur" />
                  <feOffset dx="0" dy="0" result="offsetBlur" />
                  <feComposite in="offsetBlur" in2="SourceAlpha" operator="arithmetic" k2="-1" k3="1" result="innerShadow" />
                  <feColorMatrix in="innerShadow" type="matrix" values="0 0 0 0 0.2 0 0 0 0 0.96 0 0 0 0 0.84 0 0 0 0.55 0" />
                </filter>
              </defs>
              <path
                d="M46 74 L184 58 L214 84 V194 L176 214 L42 198 L30 182 V96 Z"
                className="fill-[url(#chart-body)] stroke-[url(#chart-rim)]"
                strokeWidth={4}
                filter="url(#inner-glow)"
              />
              <path d="M46 74 L184 58 L214 84 L78 94 Z" className="fill-white/10" />
              <path d="M214 84 V194 L176 214 V110 Z" className="fill-white/5" />
              <g className="text-left">
                {[0, 25, 50, 75, 100].map((value) => {
                  const y = 188 - (value / 100) * 96;
                  return (
                    <g key={`tick-${value}`} transform={`translate(0 ${y})`}>
                      <line x1={58} x2={196} stroke="rgba(255,255,255,0.14)" strokeWidth={1.5} />
                      <text x={222} dy="5" className="fill-white/70 text-[13px] font-medium">
                        {value}%
                      </text>
                    </g>
                  );
                })}
              </g>
              <g ref={chartFillRef} clipPath="url(#liquid-clip)">
                <g ref={waveBobRef}>
                  <g>
                    <path
                      ref={wavePrimaryRef}
                      d="M0 120 C 40 104 80 136 120 120 C 160 104 200 136 240 120 C 280 104 320 136 360 120 V240 H0 Z"
                      fill="url(#liquid-gradient)"
                      opacity={0.92}
                    />
                    <path
                      ref={waveSecondaryRef}
                      d="M-80 124 C -40 108 0 140 40 124 C 80 108 120 140 160 124 C 200 108 240 140 280 124 C 320 108 360 140 400 124 V240 H-80 Z"
                      fill="url(#liquid-gradient)"
                      opacity={0.75}
                    />
                  </g>
                  <rect x={20} y={40} width={260} height={200} fill="url(#liquid-highlight)" opacity={0.35} />
                </g>
              </g>
              <path d="M46 74 L184 58" stroke="rgba(255,255,255,0.4)" strokeWidth={2.4} strokeLinecap="round" />
              <path d="M214 84 L176 214" stroke="rgba(15,118,110,0.35)" strokeWidth={3} strokeLinecap="round" />
            </svg>
          </div>
          <div className="mt-8 flex flex-col items-center gap-3">
            <span ref={percentageRef} className="text-6xl font-semibold tracking-tight text-white drop-shadow">
              0%
            </span>
            <span className="text-base font-medium uppercase tracking-[0.3em] text-emerald-200/80">
              Liquidity channels priming
            </span>
          </div>
        </div>
        <p className="relative max-w-2xl text-sm text-white/70">
          We&apos;re synchronizing your personalized analytics workspace to ensure real-time risk signals and
          market intelligence are ready the moment you arrive.
        </p>
      </div>
    </div>
  );
}

export default LandingPreloader;
