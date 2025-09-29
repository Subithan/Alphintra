'use client';

import { useEffect, useMemo, useRef } from 'react';
import { gsap } from 'gsap';

const clampProgress = (value: number) => Math.min(100, Math.max(0, value));

const CHART_HEIGHT = 240;
const waveColors = [
  'url(#water-fill)',
  'url(#water-fill-secondary)',
  'url(#water-fill-tertiary)',
];

const candleData = [
  { x: 36, bodyHeight: 82, wickHeight: 112 },
  { x: 66, bodyHeight: 68, wickHeight: 92 },
  { x: 96, bodyHeight: 116, wickHeight: 150 },
  { x: 126, bodyHeight: 74, wickHeight: 110 },
  { x: 156, bodyHeight: 94, wickHeight: 138 },
  { x: 186, bodyHeight: 62, wickHeight: 96 },
];

type LandingPreloaderProps = {
  progress: number;
  isReady: boolean;
};

export function LandingPreloader({ progress, isReady }: LandingPreloaderProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const waterGroupRef = useRef<SVGGElement>(null);
  const highlightRef = useRef<SVGPathElement>(null);
  const rippleRef = useRef<SVGCircleElement>(null);
  const percentageRef = useRef<HTMLSpanElement>(null);
  const percentageTween = useRef({ value: 0 });
  const completionTimeline = useRef<gsap.core.Timeline | null>(null);
  const waveRefs = useRef<(SVGPathElement | null)[]>([]);

  const normalizedProgress = useMemo(() => clampProgress(progress), [progress]);

  const setWaveRef = (index: number) => (node: SVGPathElement | null) => {
    waveRefs.current[index] = node;
  };

  useEffect(() => {
    if (!overlayRef.current || !waterGroupRef.current) {
      return;
    }

    const ctx = gsap.context(() => {
      gsap.set(overlayRef.current, { autoAlpha: 1 });
      gsap.set(waterGroupRef.current, { y: CHART_HEIGHT });
      if (highlightRef.current) {
        gsap.set(highlightRef.current, { y: CHART_HEIGHT - 16, autoAlpha: 0.95 });
      }
      if (rippleRef.current) {
        gsap.set(rippleRef.current, { scale: 0.8, autoAlpha: 0, transformOrigin: '50% 50%' });
      }

      waveRefs.current.forEach((wave, index) => {
        if (!wave) {
          return;
        }

        gsap.set(wave, { transformOrigin: '50% 50%' });
        gsap.to(wave, {
          duration: 6 + index * 0.5,
          x: index % 2 === 0 ? -120 : 120,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
        });
        gsap.to(wave, {
          duration: 4 + index,
          y: '+=10',
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
        });
      });
    }, overlayRef);

    return () => {
      ctx.revert();
    };
  }, []);

  useEffect(() => {
    if (!waterGroupRef.current) {
      return;
    }

    const targetY = CHART_HEIGHT - (normalizedProgress / 100) * CHART_HEIGHT;

    gsap.to(waterGroupRef.current, {
      y: targetY,
      duration: 1.1,
      ease: 'power3.out',
    });

    if (highlightRef.current) {
      gsap.to(highlightRef.current, {
        y: targetY - 18,
        duration: 1,
        ease: 'power3.out',
      });
    }
  }, [normalizedProgress]);

  useEffect(() => {
    if (!percentageRef.current) {
      return;
    }

    const target = percentageTween.current;

    gsap.to(target, {
      value: normalizedProgress,
      duration: 0.7,
      ease: 'power3.out',
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
      const timeline = gsap.timeline();
      if (waterGroupRef.current) {
        timeline.to(waterGroupRef.current, {
          duration: 0.7,
          y: -12,
          ease: 'power3.out',
        });
      }
      if (highlightRef.current) {
        timeline.to(
          highlightRef.current,
          {
            duration: 0.6,
            y: '-=18',
            ease: 'power3.out',
          },
          '<',
        );
      }
      if (rippleRef.current) {
        timeline
          .fromTo(
            rippleRef.current,
            { autoAlpha: 0, scale: 0.85 },
            { autoAlpha: 0.75, scale: 1.2, duration: 0.45, ease: 'power1.out' },
            '<',
          )
          .to(
            rippleRef.current,
            {
              duration: 1.2,
              autoAlpha: 0,
              scale: 2.2,
              ease: 'power2.out',
            },
            '-=0.2',
          );
      }
      timeline.to(
        overlayRef.current,
        {
          duration: 0.8,
          autoAlpha: 0,
          pointerEvents: 'none',
          ease: 'power2.out',
        },
        '-=0.35',
      );
      completionTimeline.current = timeline;
    } else {
      completionTimeline.current?.kill();
      gsap.to(overlayRef.current, {
        duration: 0.4,
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
      className="fixed inset-0 z-50 flex items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.35),_transparent_55%),_linear-gradient(145deg,_#020817_5%,_#041b25_40%,_#020617_100%)] text-primary-foreground"
    >
      <div className="flex w-full max-w-5xl flex-col items-center gap-12 px-6 py-16 text-center">
        <div className="w-full max-w-3xl rounded-[2.5rem] border border-white/10 bg-white/5 p-10 shadow-[0_40px_120px_rgba(9,35,51,0.45)] backdrop-blur-xl">
          <div className="mb-8 flex flex-col items-center gap-3">
            <span className="rounded-full bg-emerald-500/10 px-4 py-1 text-xs font-semibold uppercase tracking-[0.4em] text-emerald-200/80">
              Initializing marketsphere
            </span>
            <h2 className="text-3xl font-semibold text-white/90">Modeling liquidity gradients</h2>
            <p className="max-w-xl text-sm text-white/70">
              Generating multidimensional signals and syncing institutional-grade datasets to prime your trading
              cockpit.
            </p>
          </div>
          <div className="relative mx-auto flex w-full max-w-[28rem] items-center justify-center">
            <svg
              viewBox="0 0 320 360"
              role="img"
              aria-label={`Loading ${Math.round(normalizedProgress)} percent`}
              className="h-full w-full"
            >
              <defs>
                <linearGradient id="chart-border" x1="0" x2="1" y1="1" y2="0">
                  <stop offset="0%" stopColor="rgba(21, 128, 61, 0.25)" />
                  <stop offset="50%" stopColor="rgba(56, 189, 248, 0.35)" />
                  <stop offset="100%" stopColor="rgba(16, 185, 129, 0.65)" />
                </linearGradient>
                <linearGradient id="chart-bg" x1="0" x2="0" y1="1" y2="0">
                  <stop offset="0%" stopColor="rgba(2, 10, 25, 0.9)" />
                  <stop offset="100%" stopColor="rgba(4, 36, 45, 0.9)" />
                </linearGradient>
                <linearGradient id="water-fill" x1="0" x2="0" y1="1" y2="0">
                  <stop offset="0%" stopColor="rgba(0, 88, 60, 0.95)" />
                  <stop offset="70%" stopColor="rgba(16, 185, 129, 0.95)" />
                  <stop offset="100%" stopColor="rgba(236, 255, 246, 0.9)" />
                </linearGradient>
                <linearGradient id="water-fill-secondary" x1="0" x2="0" y1="1" y2="0">
                  <stop offset="0%" stopColor="rgba(0, 77, 53, 0.8)" />
                  <stop offset="65%" stopColor="rgba(12, 164, 111, 0.9)" />
                  <stop offset="100%" stopColor="rgba(206, 255, 234, 0.85)" />
                </linearGradient>
                <linearGradient id="water-fill-tertiary" x1="0" x2="0" y1="1" y2="0">
                  <stop offset="0%" stopColor="rgba(0, 61, 45, 0.75)" />
                  <stop offset="60%" stopColor="rgba(10, 142, 101, 0.85)" />
                  <stop offset="100%" stopColor="rgba(186, 255, 230, 0.78)" />
                </linearGradient>
                <linearGradient id="water-top" x1="0" x2="0" y1="1" y2="0">
                  <stop offset="0%" stopColor="rgba(255, 255, 255, 0.0)" />
                  <stop offset="45%" stopColor="rgba(255, 255, 255, 0.35)" />
                  <stop offset="100%" stopColor="rgba(255, 255, 255, 0.7)" />
                </linearGradient>
                <filter id="inner-glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="12" result="glow" />
                  <feComposite in="glow" in2="SourceAlpha" operator="arithmetic" k2="-1" k3="1" />
                </filter>
                <clipPath id="chart-window">
                  <rect x="44" y="40" width="232" height="240" rx="32" ry="32" />
                </clipPath>
              </defs>
              <rect x="36" y="28" width="248" height="268" rx="40" ry="40" fill="url(#chart-bg)" />
              <rect
                x="36"
                y="28"
                width="248"
                height="268"
                rx="40"
                ry="40"
                fill="none"
                stroke="url(#chart-border)"
                strokeWidth="3"
              />
              <g clipPath="url(#chart-window)">
                <rect x="44" y="40" width="232" height="240" fill="rgba(2,12,32,0.75)" />
                {[0, 1, 2, 3, 4, 5].map((index) => (
                  <line
                    key={`grid-horizontal-${index}`}
                    x1="44"
                    x2="276"
                    y1={40 + index * 48}
                    y2={40 + index * 48}
                    stroke="rgba(148, 163, 184, 0.18)"
                    strokeWidth="1"
                  />
                ))}
                {[0, 1, 2, 3, 4, 5, 6].map((index) => (
                  <line
                    key={`grid-vertical-${index}`}
                    x1={44 + index * 38}
                    x2={44 + index * 38}
                    y1="40"
                    y2="280"
                    stroke="rgba(30, 64, 175, 0.15)"
                    strokeWidth="1"
                  />
                ))}
                {candleData.map((candle, index) => (
                  <g key={`candle-${index}`} transform={`translate(${candle.x} 64)`}>
                    <line
                      x1="0"
                      x2="0"
                      y1={-candle.wickHeight * 0.5}
                      y2={candle.wickHeight * 0.55}
                      stroke="rgba(203, 213, 225, 0.25)"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                    <rect
                      x="-8"
                      y={-candle.bodyHeight * 0.5}
                      width="16"
                      height={candle.bodyHeight}
                      rx="4"
                      fill="rgba(125, 211, 252, 0.35)"
                      stroke="rgba(56, 189, 248, 0.45)"
                      strokeWidth="2"
                    />
                  </g>
                ))}
                <g ref={waterGroupRef} filter="url(#inner-glow)">
                  {waveColors.map((fill, index) => (
                    <path
                      key={`wave-${index}`}
                      ref={setWaveRef(index)}
                      d="M-80 220 Q -20 200 40 220 T 160 220 T 280 220 L 320 320 L -120 320 Z"
                      fill={fill}
                      opacity={0.66 - index * 0.12}
                    />
                  ))}
                </g>
                <path
                  ref={highlightRef}
                  d="M44 210 Q 160 196 276 212 L 276 228 Q 160 212 44 226 Z"
                  fill="url(#water-top)"
                  opacity="0.9"
                />
                <circle ref={rippleRef} cx="160" cy="220" r="90" fill="rgba(167, 243, 208, 0.18)" />
              </g>
              <text
                x="50"
                y="316"
                className="fill-emerald-200/80 text-[14px] tracking-[0.25em] uppercase"
              >
                Liquidity charge level
              </text>
              <text x="50" y="336" className="fill-white/60 text-[13px]">
                AI strategy stack alignment in progress
              </text>
            </svg>
          </div>
          <div className="mt-10 flex flex-col items-center gap-2">
            <span ref={percentageRef} className="text-6xl font-extrabold tracking-tight text-emerald-200">
              0%
            </span>
            <span className="text-base font-medium text-white/80">Stabilizing predictive liquidity curves…</span>
          </div>
        </div>
        <p className="max-w-2xl text-sm text-white/70">
          This immersive visualization mirrors capital inflow projections while we ready cross-venue execution,
          sentiment models, and compliance safeguards tailored to your portfolio.
        </p>
      </div>
    </div>
  );
}

export default LandingPreloader;
