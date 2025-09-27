"use client";

import { useEffect, useRef, useState } from "react";

export type BotStatus = "connecting" | "syncing" | "online";

export function useBotProgress(durationMs: number = 7000) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<BotStatus>("connecting");
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const start = performance.now();
    const tick = () => {
      const now = performance.now();
      const t = Math.min(1, (now - start) / durationMs);

      // Ease-in-out for nicer ramp
      const eased = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
      const value = Math.round(eased * 100);

      if (value < 60) setStatus("connecting");
      else if (value < 99) setStatus("syncing");
      else setStatus("online");

      setProgress(value);

      if (t < 1) requestAnimationFrame(tick);
    };

    const id = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(id);
  }, [durationMs]);

  return { progress, status };
}
