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
  const percentageRef = useRef<HTMLSpanElement>(null);
  const percentageTween = useRef({ value: 0 });
  const completionTimeline = useRef<gsap.core.Timeline | null>(null);
  const floatingTween = useRef<gsap.core.Tween | null>(null);
  const waveRefs = useRef<(SVGGElement | null)[]>([]);
  const sparkleRefs = useRef<(SVGCircleElement | null)[]>([]);
  const chartCardRef = useRef<HTMLDivElement>(null);

  const normalizedProgress = useMemo(() => clampProgress(progress), [progress]);

  useEffect(() => {
    if (!overlayRef.current || !chartFillRef.current) {
      return;
    }

    const ctx = gsap.context(() => {
      gsap.set(chartFillRef.current, { yPercent: 100, transformOrigin: '50% 100%' });
      gsap.set(overlayRef.current, { autoAlpha: 1 });
      gsap.set(chartCardRef.current, { y: 0, rotateX: 0 });
    }, overlayRef);

    return () => ctx.revert();
  }, []);

  useEffect(() => {
    if (!chartCardRef.current) {
      return;
    }

    const ctx = gsap.context(() => {
      floatingTween.current = gsap.to(chartCardRef.current, {
        y: -10,
        rotateX: -4,
        duration: 5.5,
        ease: 'sine.inOut',
        repeat: -1,
        yoyo: true,
      });
    }, chartCardRef);

    return () => {
      floatingTween.current?.kill();
      floatingTween.current = null;
      ctx.revert();
    };
  }, []);

  useEffect(() => {
    if (!chartFillRef.current) {
      return;
    }

    gsap.to(chartFillRef.current, {
      yPercent: 100 - normalizedProgress,
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
      floatingTween.current?.pause();
      completionTimeline.current = gsap.timeline();
      completionTimeline.current
        .to(
          chartCardRef.current,
          {
            duration: 0.6,
            y: -12,
            rotateX: -6,
            ease: 'expo.out',
          },
          0,
        )
        .to(
          chartFillRef.current,
          {
            duration: 0.6,
            yPercent: 0,
            ease: 'power3.out',
          },
          0,
        )
        .to(
          overlayRef.current,
          {
            duration: 0.6,
            autoAlpha: 0,
            pointerEvents: 'none',
            ease: 'power2.out',
          },
          '-=0.1',
        );
    } else {
      completionTimeline.current?.kill();
      gsap.to(overlayRef.current, {
        duration: 0.3,
        autoAlpha: 1,
        pointerEvents: 'auto',
      });
      gsap.to(chartCardRef.current, {
        duration: 0.6,
        y: 0,
        rotateX: 0,
        ease: 'expo.out',
      });
      floatingTween.current?.resume();
    }
  }, [isReady]);

  useEffect(() => {
    const activeWaveRefs = waveRefs.current.filter(Boolean);

    if (!activeWaveRefs.length) {
      return;
    }

    const waveTimeline = gsap.context(() => {
      activeWaveRefs.forEach((wave, index) => {
        gsap.to(wave, {
          xPercent: index % 2 === 0 ? -50 : -65,
          duration: 6 + index * 2,
          ease: 'none',
          repeat: -1,
        });

        gsap.to(wave, {
          y: index % 2 === 0 ? 4 : -4,
          duration: 3 + index,
          repeat: -1,
          yoyo: true,
          ease: 'sine.inOut',
          delay: index * 0.3,
        });
      });
    }, overlayRef);

    return () => waveTimeline.revert();
  }, []);

  useEffect(() => {
    const activeSparkles = sparkleRefs.current.filter(Boolean);

    if (!activeSparkles.length) {
      return;
    }

    const sparkleTimeline = gsap.context(() => {
      activeSparkles.forEach((sparkle, index) => {
        gsap.set(sparkle, { opacity: 0 });
        gsap.to(sparkle, {
          keyframes: [
            { opacity: 0, scale: 0.6 },
            { opacity: 0.9, scale: 1.1, duration: 0.3 },
            { opacity: 0, scale: 0.4, duration: 0.5 },
          ],
          delay: index * 0.5,
          repeat: -1,
          repeatDelay: 2.2,
          ease: 'power1.out',
        });
      });
    }, overlayRef);

    return () => sparkleTimeline.revert();
  }, []);

  const registerWave = (index: number) => (element: SVGGElement | null) => {
    waveRefs.current[index] = element;
  };

  const registerSparkle = (index: number) => (element: SVGCircleElement | null) => {
    sparkleRefs.current[index] = element;
  };

  const chartPath = useMemo(
    () =>
      'M24 184V84l18-28h24v46l28-36h22v64l30-40h18v94z',
    [],
  );

  useEffect(() => () => completionTimeline.current?.kill(), []);

  return (
    <div
      ref={overlayRef}
      role="status"
      aria-live="polite"
      aria-busy={!isReady}
      className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-[#020617] via-[#001220] to-[#012921] text-primary-foreground"
    >
      <div className="flex w-full max-w-4xl flex-col items-center gap-12 px-6 py-10 text-center text-white">
        <div
          ref={chartCardRef}
          className="relative mx-auto flex max-w-2xl flex-col items-center gap-8 rounded-[32px] border border-emerald-300/20 bg-white/5 p-10 shadow-[0_30px_60px_-20px_rgba(0,0,0,0.75)] backdrop-blur-xl transition-transform"
        >
          <div className="text-xs font-semibold uppercase tracking-[0.35em] text-emerald-100/90">
            Preparing your trading intelligence
          </div>
          <div className="relative flex h-[18rem] w-[18rem] items-center justify-center">
            <svg
              viewBox="0 0 220 220"
              role="img"
              aria-label={`Loading ${Math.round(normalizedProgress)} percent`}
              className="h-full w-full drop-shadow-[0_25px_40px_rgba(16,185,129,0.35)]"
            >
              <defs>
                <linearGradient id="chart-outline" x1="0" x2="1" y1="0" y2="1">
                  <stop offset="0%" stopColor="rgba(148, 163, 184, 0.7)" />
                  <stop offset="100%" stopColor="rgba(226, 255, 243, 0.25)" />
                </linearGradient>
                <linearGradient id="water-fill" x1="0" x2="0" y1="1" y2="0">
                  <stop offset="0%" stopColor="rgba(6, 95, 70, 0.95)" />
                  <stop offset="45%" stopColor="rgba(16, 185, 129, 0.9)" />
                  <stop offset="90%" stopColor="rgba(134, 239, 172, 0.7)" />
                </linearGradient>
                <radialGradient id="water-highlight" cx="0.6" cy="0.1" r="0.8">
                  <stop offset="0%" stopColor="rgba(240, 253, 244, 0.9)" />
                  <stop offset="45%" stopColor="rgba(134, 239, 172, 0.35)" />
                  <stop offset="100%" stopColor="rgba(16, 185, 129, 0)" />
                </radialGradient>
                <linearGradient id="grid-line" x1="0" x2="1" y1="0" y2="0">
                  <stop offset="0%" stopColor="rgba(203, 213, 225, 0)" />
                  <stop offset="40%" stopColor="rgba(203, 213, 225, 0.2)" />
                  <stop offset="100%" stopColor="rgba(203, 213, 225, 0)" />
                </linearGradient>
                <clipPath id="chart-clip">
                  <path d={chartPath} />
                </clipPath>
                <filter id="glass-glow" x="-30%" y="-30%" width="160%" height="160%">
                  <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur" />
                  <feColorMatrix
                    in="blur"
                    type="matrix"
                    values="0 0 0 0 0.15  0 0 0 0 0.45  0 0 0 0 0.33  0 0 0 0.8 0"
                  />
                </filter>
              </defs>
              <g transform="translate(18 16)">
                <path
                  d="M0 0h184c8.8 0 16 7.2 16 16v164c0 8.8-7.2 16-16 16H0c-8.8 0-16-7.2-16-16V16C-16 7.2-8.8 0 0 0z"
                  fill="rgba(2, 44, 34, 0.85)"
                  stroke="url(#chart-outline)"
                  strokeWidth="3"
                  opacity="0.7"
                  filter="url(#glass-glow)"
                />
                <g clipPath="url(#chart-clip)">
                  <rect x="-10" y="-10" width="240" height="240" fill="rgba(2, 80, 48, 0.4)" />
                  <g ref={chartFillRef}>
                    <rect x="-10" y="-10" width="240" height="240" fill="url(#water-fill)" />
                    <g ref={registerWave(0)}>
                      <path
                        d="M0 60 Q 30 50 60 60 T 120 60 T 180 60 T 240 60 V240 H0 Z"
                        fill="rgba(34, 197, 94, 0.75)"
                      />
                    </g>
                    <g ref={registerWave(1)}>
                      <path
                        d="M0 70 Q 30 82 60 70 T 120 70 T 180 70 T 240 70 V240 H0 Z"
                        fill="rgba(16, 185, 129, 0.55)"
                      />
                    </g>
                    <g ref={registerWave(2)}>
                      <path
                        d="M0 80 Q 35 92 70 80 T 140 80 T 210 80 T 280 80 V240 H0 Z"
                        fill="rgba(52, 211, 153, 0.35)"
                      />
                    </g>
                    <rect x="-10" y="-20" width="240" height="120" fill="url(#water-highlight)" opacity="0.85" />
                  </g>
                  <rect x="-10" y="-10" width="240" height="240" fill="url(#water-highlight)" opacity="0.12" />
                </g>
                <path
                  d={chartPath}
                  fill="none"
                  stroke="rgba(110, 231, 183, 0.45)"
                  strokeWidth="3"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />
                <g opacity="0.9">
                  {[1, 2, 3, 4, 5, 6].map((index) => (
                    <line
                      key={`grid-${index}`}
                      x1="-6"
                      x2="206"
                      y1={28 * index}
                      y2={28 * index}
                      stroke="url(#grid-line)"
                      strokeWidth="1.5"
                    />
                  ))}
                </g>
                <g fontFamily="'Inter', sans-serif" fontSize="12" fill="rgba(226, 252, 239, 0.65)" textAnchor="start">
                  {[0, 25, 50, 75, 100].map((value) => (
                    <text key={`label-${value}`} x="190" y={188 - (value / 100) * 140} dy="4">
                      {value}%
                    </text>
                  ))}
                </g>
                {[0, 1, 2, 3].map((index) => (
                  <circle
                    key={`sparkle-${index}`}
                    ref={registerSparkle(index)}
                    cx={120 + index * 12}
                    cy={84 - index * 10}
                    r={index % 2 === 0 ? 2.8 : 3.6}
                    fill="rgba(226, 252, 239, 0.85)"
                  />
                ))}
              </g>
            </svg>
          </div>
          <div className="flex flex-col items-center gap-3">
            <span ref={percentageRef} className="text-6xl font-bold tracking-tight text-emerald-100 drop-shadow-lg">
              0%
            </span>
            <span className="text-base font-medium text-emerald-50/80">Calibrating predictive indices…</span>
          </div>
        </div>
        <p className="max-w-2xl text-sm text-emerald-100/70">
          We&apos;re synchronizing your personalized analytics workspace to ensure real-time risk signals and market
          intelligence are ready the moment you arrive.
        </p>
      </div>
    </div>
  );
}

export default LandingPreloader;
