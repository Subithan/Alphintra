'use client';

import { useEffect, useMemo, useRef } from 'react';
import { gsap } from 'gsap';

type LandingPreloaderProps = {
  progress: number;
  isReady: boolean;
};

const clampProgress = (value: number) => Math.min(100, Math.max(0, value));

export function LandingPreloader({ progress, isReady }: LandingPreloaderProps) {
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const percentTextRef = useRef<HTMLDivElement | null>(null);
  const timelineRef = useRef<gsap.core.Timeline | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const normalizedProgress = useMemo(() => clampProgress(progress), [progress]);

  // Fade-in / out overlay on readiness
  useEffect(() => {
    if (!overlayRef.current) return;

    if (isReady) {
      timelineRef.current?.kill();
      timelineRef.current = gsap.timeline();
      timelineRef.current.to(overlayRef.current, {
        duration: 0.6,
        autoAlpha: 0,
        pointerEvents: 'none',
        ease: 'power2.out',
      });
    } else {
      gsap.set(overlayRef.current, { autoAlpha: 1, pointerEvents: 'auto' });
    }
  }, [isReady]);

  // Update percentage text content
  useEffect(() => {
    if (percentTextRef.current) {
      percentTextRef.current.textContent = `${Math.round(normalizedProgress)}%`;
    }
  }, [normalizedProgress]);

  // Glowing particle background on canvas (black theme)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let raf = 0;
    let running = true;

    const DPR = Math.min(window.devicePixelRatio || 1, 2);
    const particles: { x: number; y: number; vx: number; vy: number; r: number; a: number; t: number }[] = [];

    const resize = () => {
      const { innerWidth: w, innerHeight: h } = window;
      canvas.width = Math.floor(w * DPR);
      canvas.height = Math.floor(h * DPR);
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    };
    resize();
    window.addEventListener('resize', resize);

    const count = Math.min(220, Math.floor((window.innerWidth * window.innerHeight) / 7000));
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
        r: 0.8 + Math.random() * 1.8,
        a: 0.6 + Math.random() * 0.8,
        t: Math.random() * Math.PI * 2,
      });
    }

    const step = () => {
      if (!running) return;
      // background
      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // glowing particles
      ctx.globalCompositeOperation = 'lighter';
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.t += 0.015;
        const twinkle = 0.8 + 0.2 * Math.sin(p.t);
        const rr = p.r * (2.8 + Math.sin(p.t * 2) * 0.6);
        if (p.x < -10) p.x = window.innerWidth + 10;
        if (p.x > window.innerWidth + 10) p.x = -10;
        if (p.y < -10) p.y = window.innerHeight + 10;
        if (p.y > window.innerHeight + 10) p.y = -10;

        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, rr);
        const base = Math.min(1, Math.max(0, 0.5 + 0.5 * p.a * twinkle));
        grad.addColorStop(0, `rgba(170,210,255,${0.85 * base})`);
        grad.addColorStop(0.35, `rgba(80,160,255,${0.45 * base})`);
        grad.addColorStop(1, 'rgba(80,160,255,0)');

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(p.x, p.y, rr, 0, Math.PI * 2);
        ctx.fill();
      }

      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
    };
  }, []);

  // Progress bar width & star position are derived directly in JSX using normalizedProgress

  return (
    <div
      ref={overlayRef}
      role="status"
      aria-live="polite"
      aria-busy={!isReady}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black text-white"
      style={{ opacity: 1 }}
    >
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />

      <div className="relative z-10 flex w-screen max-w-none flex-col items-center gap-6 px-0">
        <div className="text-sm tracking-widest text-neutral-300">Loading…</div>

        <div className="relative w-full h-[10px] sm:h-3">
          {/* Track */}
          <div className="absolute inset-0 rounded-full bg-neutral-950 border border-neutral-800 overflow-hidden shadow-[0_0_0_1px_rgba(255,255,255,0.05)_inset]">
            {/* Fill */}
            <div
              className="absolute left-0 top-0 h-full rounded-full"
              style={{
                width: `${normalizedProgress}%`,
                background:
                  'linear-gradient(90deg, rgba(60,60,60,0.7) 0%, rgba(120,120,120,0.9) 60%, rgba(180,180,180,1) 100%)',
                boxShadow: '0 0 12px rgba(180,180,180,0.35) inset',
              }}
              aria-hidden
            />
          </div>

          {/* Glowing star (not clipped by overflow) */}
          <div
            className="absolute -top-3 w-9 h-9 -translate-x-1/2 select-none pointer-events-none"
            style={{ left: `${normalizedProgress}%` }}
            aria-hidden
          >
            <svg
              viewBox="0 0 64 64"
              className="w-9 h-9"
              style={{ filter: 'drop-shadow(0 0 8px rgba(160,200,255,0.95)) drop-shadow(0 0 18px rgba(120,180,255,0.8)) drop-shadow(0 0 28px rgba(80,140,255,0.65))' }}
            >
              <defs>
                <radialGradient id="star-glow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
                  <stop offset="60%" stopColor="#e5e5e5" stopOpacity="0.9" />
                  <stop offset="100%" stopColor="#ffffff" stopOpacity="0.0" />
                </radialGradient>
              </defs>
              <g>
                <circle cx="32" cy="32" r="18" fill="url(#star-glow)" />
                <path
                  d="M32 6 L36 26 L58 32 L36 38 L32 58 L28 38 L6 32 L28 26 Z"
                  fill="#ffffff"
                />
              </g>
            </svg>
          </div>
        </div>

        <div className="flex items-center gap-2 text-neutral-300">
          <div ref={percentTextRef} className="text-2xl font-semibold">0%</div>
        </div>
      </div>
    </div>
  );
}

export default LandingPreloader;
