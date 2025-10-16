"use client";

import { Zap } from "lucide-react";
import React, { useCallback, useEffect, useMemo, useRef } from "react";
import Loader from "@/components/ui/Loader";
import { useBotProgress } from "@/components/hooks/useBotProgress";

type PixelRepelTextProps = {
  text: string;
  className?: string;
  radius?: number;
  strength?: number;
  spring?: number;
  damping?: number;
  glow?: string;
  idleGlow?: string;
};

type CharState = {
  x: number;
  y: number;
  vx: number;
  vy: number;
};

type RenderToken =
  | { type: 'char'; value: string }
  | { type: 'break' };

const PixelRepelText: React.FC<PixelRepelTextProps> = ({
  text,
  className,
  radius = 260,
  strength = 38,
  spring = 0.18,
  damping = 0.82,
  glow = '0 0 16px rgba(250,204,21,0.45)',
  idleGlow = '0 0 8px rgba(250,204,21,0.2)',
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const charRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const statesRef = useRef<CharState[]>([]);
  const pointerRef = useRef<{ x: number; y: number } | null>(null);
  const frameRef = useRef<number | null>(null);

  const normalized = useMemo(() => {
  return text.split('\r\n').join('\n').split('\r').join('\n');
}, [text]);
const lines = useMemo(() => normalized.split('\n'), [normalized]);
const charCount = useMemo(() => lines.reduce((acc, line) => acc + line.length, 0), [lines]);

  useEffect(() => {
    statesRef.current = Array.from({ length: charCount }, () => ({ x: 0, y: 0, vx: 0, vy: 0 }));
    charRefs.current = Array.from({ length: charCount }, () => null);
    pointerRef.current = null;
    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
  }, [charCount]);

  const animate = useCallback(() => {
    frameRef.current = null;
    const pointer = pointerRef.current;
    let active = false;

    statesRef.current.forEach((state, index) => {
      const node = charRefs.current[index];
      if (!node) {
        return;
      }

      const rect = node.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;

      let fx = -state.x * spring;
      let fy = -state.y * spring;

      if (pointer) {
        const dx = cx - pointer.x;
        const dy = cy - pointer.y;
        const dist = Math.hypot(dx, dy);
        if (dist < radius) {
          const influence = (1 - dist / radius) ** 2;
          const force = strength * influence;
          fx += (dx / (dist || 1)) * force;
          fy += (dy / (dist || 1)) * force;
        }
      }

      state.vx = (state.vx + fx) * damping;
      state.vy = (state.vy + fy) * damping;
      state.x += state.vx;
      state.y += state.vy;

      if (
        Math.abs(state.vx) > 0.04 ||
        Math.abs(state.vy) > 0.04 ||
        Math.abs(state.x) > 0.25 ||
        Math.abs(state.y) > 0.25 ||
        pointer
      ) {
        active = true;
      }

      node.style.transform = `translate3d(${state.x.toFixed(2)}px, ${state.y.toFixed(2)}px, 0)`;
      node.style.textShadow = pointer ? glow : idleGlow;
    });

    if (active) {
      frameRef.current = requestAnimationFrame(animate);
    } else {
      charRefs.current.forEach((node) => {
        if (node) node.style.textShadow = idleGlow;
      });
    }
  }, [radius, strength, spring, damping, glow, idleGlow]);

  const ensureAnimating = useCallback(() => {
    if (frameRef.current === null) {
      frameRef.current = requestAnimationFrame(animate);
    }
  }, [animate]);

  const updatePointer = useCallback(
    (clientX: number, clientY: number) => {
      const container = containerRef.current;
      if (!container) return;
      pointerRef.current = { x: clientX, y: clientY };
      ensureAnimating();
    },
    [ensureAnimating],
  );

  const handlePointerMove = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      updatePointer(event.clientX, event.clientY);
    },
    [updatePointer],
  );

  const handleTouchMove = useCallback(
    (event: React.TouchEvent<HTMLDivElement>) => {
      const touch = event.touches[0] ?? event.changedTouches[0];
      if (!touch) return;
      updatePointer(touch.clientX, touch.clientY);
    },
    [updatePointer],
  );

  const handleLeave = useCallback(() => {
    pointerRef.current = null;
    ensureAnimating();
  }, [ensureAnimating]);

  useEffect(() => () => {
    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
  }, []);

  let runningIndex = 0;

  return (
    <div
      ref={containerRef}
      className={`inline-flex flex-wrap items-baseline gap-[0.08em] select-none ${className ?? ''}`}
      onPointerEnter={handlePointerMove}
      onPointerMove={handlePointerMove}
      onPointerLeave={handleLeave}
      onMouseMove={handlePointerMove}
      onMouseLeave={handleLeave}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleLeave}
      style={{ touchAction: 'none' }}
    >
      {lines.map((line, lineIndex) => (
        <React.Fragment key={`line-${lineIndex}`}>
          {[...line].map((ch, charIndex) => {
            const displayChar = ch === ' ' ? ' ' : ch.toUpperCase();
            const index = runningIndex++;
            return (
              <span
                key={`char-${lineIndex}-${charIndex}`}
                ref={(node) => {
                  charRefs.current[index] = node;
                }}
                className="inline-block will-change-transform"
                style={{ textShadow: idleGlow }}
              >
                {displayChar}
              </span>
            );
          })}
          {lineIndex !== lines.length - 1 ? (
            <span key={`break-${lineIndex}`} className="basis-full w-full h-0" aria-hidden="true" />
          ) : null}
        </React.Fragment>
      ))}
      <span className="sr-only">{text}</span>
    </div>
  );
};


export const Hero = () => {
  const { progress, status } = useBotProgress(7000);
  const paragraphText = useMemo(
    () =>
      "Create sophisticated trading strategies using our intuitive drag-and-drop interface.\nAutomate your trades with AI-powered bots – 24/7.",
    [],
  );

  return (
    <section className="text-white bg-transparent pt-24 pb-16 min-h-screen flex items-center glass-gradient">
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <defs>
          <linearGradient id="text-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style={{ stopColor: "#F87AFF" }} />
            <stop offset="25%" style={{ stopColor: "#FB93D0" }} />
            <stop offset="50%" style={{ stopColor: "#FFDD00" }} />
            <stop offset="75%" style={{ stopColor: "#C3F0B2" }} />
            <stop offset="100%" style={{ stopColor: "#2FD8FE" }} />
          </linearGradient>
        </defs>
      </svg>
      <div className="container mx-auto px-4">
        <div className="relative isolate">
          <div className="absolute inset-0 -z-20" />
          <div className="relative z-10 flex flex-col lg:flex-row items-center justify-center gap-12">
            {/* Text Column */}
            <div className="w-full lg:w-1/2">
              <div className="relative overflow-hidden rounded-2xl border border-white/15 bg-white/5 backdrop-blur-2xl shadow-[0_40px_120px_rgba(15,23,42,0.45)] px-8 py-10 max-w-xl liquid-glass">
                <div className="absolute inset-0 liquid-glass-effect" />
                <div className="relative z-10 text-left">
                  <div className="flex items-center justify-start">
                    <p className="inline-flex items-center gap-2 border py-1 px-3 rounded-lg border-white/30 bg-white/10 backdrop-blur-md text-sm uppercase tracking-wide">
                      <Zap
                        size={18}
                        className="text-transparent"
                        style={{ stroke: "url(#text-gradient)", fill: "none", strokeWidth: 1.2 }}
                        aria-hidden="true"
                      />
                      <span className="bg-[linear-gradient(to_right,#F87AFF,#FB93D0,#FFDD00,#C3F0B2,#2FD8FE)] text-transparent bg-clip-text [-webkit-background-clip:text]">
                        No-Code Trading Automation
                      </span>
                    </p>
                  </div>

                  <div className="mt-6 space-y-6">
                    <PixelRepelText
                      text="Build Trading Bots"
                      className="font-pixel uppercase text-4xl sm:text-5xl lg:text-6xl tracking-[0.2em] text-gray-100"
                      radius={320}
                      strength={42}
                      spring={0.2}
                      damping={0.84}
                    />
                    <PixelRepelText
                      text="Without Code"
                      className="font-pixel uppercase text-4xl sm:text-5xl lg:text-6xl tracking-[0.2em] text-gray-100"
                      radius={320}
                      strength={42}
                      spring={0.2}
                      damping={0.84}
                    />
                  </div>

                  <PixelRepelText
                    text={paragraphText}
                    className="mt-8 block max-w-xl font-pixel uppercase text-sm sm:text-base tracking-[0.1em] leading-relaxed text-gray-100/85"
                    radius={260}
                    strength={28}
                    spring={0.18}
                    damping={0.86}
                    glow="0 0 10px rgba(250,204,21,0.35)"
                    idleGlow="0 0 6px rgba(250,204,21,0.2)"
                  />

                  <div className="mt-10">
                    <button
                      type="button"
                      className="relative inline-flex items-center justify-center rounded-xl px-6 py-3 text-lg font-semibold text-slate-900 focus:outline-none"
                      aria-label="Get started with trading automation"
                    >
                      <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-yellow-300 via-amber-400 to-yellow-500" aria-hidden />
                      <span className="absolute inset-0 rounded-xl blur-md opacity-60 bg-yellow-300/50" aria-hidden />
                      <span className="relative">Get Started</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Visual Column */}
            <div className="w-full lg:w-1/2 flex flex-col items-center">
              <div className="w-full max-w-[800px] h-[450px] rounded-2xl overflow-hidden border border-white/10 bg-white/5 backdrop-blur-md relative liquid-glass">
                <div className="absolute inset-0 liquid-glass-effect" />
                <div className="robot absolute inset-0">
                  <div className="robot-head mx-auto mt-10">
                    <span className="robot-eye left" />
                    <span className="robot-eye right" />
                    <span className="robot-scan" />
                  </div>
                  <div className="robot-body mx-auto">
                    <span className="robot-chest-led" />
                  </div>
                </div>

                <div className="absolute bottom-3 w-full px-4">
                  <div className="bot-loader backdrop-blur-md flex items-center justify-between gap-3 px-4 py-3 rounded-2xl w-[360px] max-w-full mx-auto">
                    <div className="flex items-center gap-2 text-sm text-gray-100 font-medium">
                      <Loader className="text-gray-100 w-4 h-4" />
                      {status === "online" ? "Bot Online" : status === "syncing" ? "Syncing" : "Starting Bot"}
                    </div>
                    <span className="text-[10px] text-gray-300">{progress}%</span>
                  </div>
                  <div className="bot-progress w-[360px] max-w-full mx-auto">
                    <div className="bot-progress-bar" style={{ width: `${Math.max(10, progress)}%` }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
