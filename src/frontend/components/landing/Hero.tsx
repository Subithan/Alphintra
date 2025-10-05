"use client";

import { Zap } from "lucide-react";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Loader from "@/components/ui/Loader";
import { useBotProgress } from "@/components/hooks/useBotProgress";

type PixelCanvasTextProps = {
  text: string;
  className?: string;
  fontSize?: number;
  sample?: number;
  pixelSize?: number;
  radius?: number;
  strength?: number;
  easing?: number;
  color?: string;
  glowColor?: string;
};

type PixelPoint = {
  x: number;
  y: number;
  offsetX: number;
  offsetY: number;
};

const PixelCanvasText: React.FC<PixelCanvasTextProps> = ({
  text,
  className,
  fontSize = 140,
  sample = 6,
  pixelSize = 4,
  radius = 260,
  strength = 36,
  easing = 0.2,
  color = "rgba(255,255,255,0.96)",
  glowColor = "rgba(250,204,21,0.4)",
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const pointsRef = useRef<PixelPoint[]>([]);
  const pointerRef = useRef<{ x: number; y: number } | null>(null);
  const animationRef = useRef<number | null>(null);
  const displayRef = useRef<{ width: number; height: number; pixel: number; dpr: number }>({
    width: 0,
    height: 0,
    pixel: pixelSize,
    dpr: 1,
  });
  const [pixelCount, setPixelCount] = useState(0);

  const draw = useCallback(() => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    const { width, height, pixel, dpr } = displayRef.current;
    ctx.save();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = color;
    ctx.shadowColor = glowColor;
    ctx.shadowBlur = Math.max(4, pixel * 1.8);
    pointsRef.current.forEach((point) => {
      ctx.fillRect(point.x + point.offsetX, point.y + point.offsetY, pixel, pixel);
    });
    ctx.restore();
  }, [color, glowColor]);

  const step = useCallback(() => {
    animationRef.current = null;
    const pointer = pointerRef.current;
    let needsNextFrame = false;

    pointsRef.current.forEach((point) => {
      let targetX = 0;
      let targetY = 0;
      if (pointer) {
        const dx = point.x - pointer.x;
        const dy = point.y - pointer.y;
        const dist = Math.hypot(dx, dy);
        if (dist < radius) {
          const power = 1 - dist / radius;
          targetX = (dx / (dist || 1)) * strength * power;
          targetY = (dy / (dist || 1)) * strength * power;
        }
      }

      point.offsetX += (targetX - point.offsetX) * easing;
      point.offsetY += (targetY - point.offsetY) * easing;

      if (Math.abs(point.offsetX) > 0.05 || Math.abs(point.offsetY) > 0.05 || pointer) {
        needsNextFrame = true;
      }
    });

    draw();

    if (needsNextFrame) {
      animationRef.current = requestAnimationFrame(step);
    }
  }, [draw, radius, strength, easing]);

  const rebuild = useCallback(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) {
      setPixelCount(0);
      return;
    }

    const temp = document.createElement("canvas");
    const ctx = temp.getContext("2d");
    if (!ctx) {
      setPixelCount(0);
      return;
    }

    const lines = text.toUpperCase().split(/\n+/);
    const pad = Math.ceil(fontSize * 0.22);
    const lineHeight = fontSize * 1.18;

    ctx.font = `${fontSize}px 'Pixelify Sans', 'JetBrains Mono', monospace`;
    ctx.textBaseline = "top";
    ctx.fillStyle = "#ffffff";

    let width = 0;
    lines.forEach((line) => {
      width = Math.max(width, ctx.measureText(line).width);
    });
    const height = lineHeight * lines.length;

    temp.width = Math.ceil(width + pad * 2);
    temp.height = Math.ceil(height + pad * 2);

    ctx.clearRect(0, 0, temp.width, temp.height);
    ctx.font = `${fontSize}px 'Pixelify Sans', 'JetBrains Mono', monospace`;

    lines.forEach((line, index) => {
      ctx.fillText(line, pad, pad + index * lineHeight);
    });

    const img = ctx.getImageData(0, 0, temp.width, temp.height);
    const data = img.data;
    const stepSize = Math.max(1, sample);
    const rawPoints: PixelPoint[] = [];

    for (let y = 0; y < img.height; y += stepSize) {
      for (let x = 0; x < img.width; x += stepSize) {
        const alpha = data[(y * img.width + x) * 4 + 3];
        if (alpha > 160) {
          rawPoints.push({ x, y, offsetX: 0, offsetY: 0 });
        }
      }
    }

    if (rawPoints.length === 0) {
      setPixelCount(0);
      return;
    }

    const containerWidth = container.getBoundingClientRect().width || temp.width;
    const scale = Math.min(1, containerWidth / temp.width);
    const displayWidth = Math.max(1, temp.width * scale);
    const displayHeight = Math.max(1, temp.height * scale);
    const dpr = Math.min(window.devicePixelRatio ?? 1, 2);

    canvas.width = Math.ceil(displayWidth * dpr);
    canvas.height = Math.ceil(displayHeight * dpr);
    canvas.style.width = `${displayWidth}px`;
    canvas.style.height = `${displayHeight}px`;

    const ctxOut = canvas.getContext("2d");
    if (!ctxOut) {
      setPixelCount(0);
      return;
    }

    ctxOut.imageSmoothingEnabled = false;
    ctxRef.current = ctxOut;

    displayRef.current = {
      width: displayWidth,
      height: displayHeight,
      pixel: Math.max(1.5, pixelSize * scale),
      dpr,
    };

    pointsRef.current = rawPoints.map((point) => ({
      x: point.x * scale,
      y: point.y * scale,
      offsetX: 0,
      offsetY: 0,
    }));

    pointerRef.current = null;
    setPixelCount(rawPoints.length);
    draw();
  }, [text, fontSize, sample, pixelSize, draw]);

  useEffect(() => {
    rebuild();

    const handleResize = () => rebuild();
    window.addEventListener("resize", handleResize);

    let cancelled = false;
    const fontReady = (document as any).fonts?.ready;
    if (fontReady) {
      fontReady.then(() => {
        if (!cancelled) rebuild();
      });
    }

    return () => {
      cancelled = true;
      window.removeEventListener("resize", handleResize);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [rebuild]);

  const handlePointerMove = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      const canvas = canvasRef.current;
      if (!canvas || pixelCount === 0) return;
      const rect = canvas.getBoundingClientRect();
      pointerRef.current = {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      };
      if (animationRef.current == null) {
        animationRef.current = requestAnimationFrame(step);
      }
    },
    [step, pixelCount],
  );

  const handlePointerLeave = useCallback(() => {
    pointerRef.current = null;
    if (animationRef.current == null) {
      animationRef.current = requestAnimationFrame(step);
    }
  }, [step]);

  if (pixelCount === 0) {
    return (
      <span className={`font-pixel uppercase tracking-[0.18em] text-inherit ${className ?? ""}`}>
        {text.toUpperCase()}
      </span>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`relative select-none ${className ?? ""}`}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
    >
      <canvas ref={canvasRef} className="block w-full h-auto" />
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
                    <PixelCanvasText
                      text="Build Trading Bots"
                      className="block w-full max-w-2xl"
                      fontSize={170}
                      sample={4}
                      pixelSize={5}
                      radius={320}
                      strength={46}
                      easing={0.18}
                    />
                    <PixelCanvasText
                      text="Without Code"
                      className="block w-full max-w-2xl"
                      fontSize={170}
                      sample={4}
                      pixelSize={5}
                      radius={320}
                      strength={46}
                      easing={0.18}
                    />
                  </div>

                  <PixelCanvasText
                    text={paragraphText}
                    className="mt-8 block w-full max-w-xl"
                    fontSize={52}
                    sample={6}
                    pixelSize={3}
                    radius={260}
                    strength={28}
                    easing={0.22}
                    color="rgba(255,255,255,0.85)"
                    glowColor="rgba(250,204,21,0.25)"
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
