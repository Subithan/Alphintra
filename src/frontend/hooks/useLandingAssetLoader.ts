"use client";

import { useEffect, useRef, useState, type ComponentType } from "react";

type CanvasComponent = ComponentType<Record<string, unknown>>;
type LoadStatus = "success" | "timeout" | "error" | "aborted" | "skipped";

const COIN_IMAGE_NAMES = [
  "AAVE.png",
  "Avalanche_Camera1.png",
  "Avax.png",
  "BNB.png",
  "BNB_Camera1.png",
  "BinanceUSD_Camera1.png",
  "Bitcoin.png",
  "Bitcoin_Camera1.png",
  "Cardano.png",
  "Cardano_Camera1.png",
  "Chainlink.png",
  "Cosmohub.png",
  "Cosmos_Camera1.png",
  "Cronos_Camera1.png",
  "DAI.png",
  "Dai_Camera5.png",
  "Dogecoin.png",
  "Dogecoin_Camera1.png",
  "EGLD.png",
  "Ethereum_Camera1.png",
  "Etherium.png",
  "FCTR.png",
  "FTN.png",
  "Filecoin.png",
  "Hashgraph.png",
  "Injective.png",
  "Jupiter.png",
  "KCS.png",
  "Litecoin.png",
  "MKR.png",
  "Mana.png",
  "Near.png",
  "Polkadot.png",
  "Polkadot_Camera1.png",
  "Polygon.png",
  "Polygon_Camera1.png",
  "ShibaInu_Camera1.png",
  "Solana.png",
  "Solana_Camera1.png",
  "Stellar.png",
  "Sushi.png",
  "TerraUSD_Camera1.png",
  "Terra_Camera1.png",
  "Tether.png",
  "Tether_Camera1.png",
  "Ton.png",
  "Tron.png",
  "USDC.png",
  "USDCoin_Camera1.png",
  "Uniswap.png",
  "VET.png",
  "WrappedBitcoin_Camera1.png",
  "XRP.png",
  "XRP_Camera1.png",
  "XTZ.png",
  "ZEC.png",
];

const IMAGE_WEIGHT = 0.6;
const FONT_WEIGHT = 0.15;
const MODULE_WEIGHT = 0.25;
const TOTAL_WEIGHT = IMAGE_WEIGHT + FONT_WEIGHT + MODULE_WEIGHT;

const IMAGE_TIMEOUT_MS = 8000;
const FONT_TIMEOUT_MS = 5000;
const IMAGE_CONCURRENCY = 6;

type LoaderOptions = {
  signal: AbortSignal;
  onProgress: (value: number) => void;
  onCanvasReady?: (component: CanvasComponent) => void;
};

type LoaderResult = {
  canvasComponent: CanvasComponent | null;
  errors: string[];
};

export function useLandingAssetLoader() {
  const [progress, setProgress] = useState(0);
  const [ready, setReady] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const canvasRef = useRef<CanvasComponent | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    const run = async () => {
      const result = await loadLandingAssets({
        signal: controller.signal,
        onProgress: (value) => {
          if (!cancelled) setProgress(value);
        },
        onCanvasReady: (component) => {
          canvasRef.current = component;
        },
      });

      if (cancelled) return;

      if (result.errors.length) {
        setErrors(result.errors);
        // eslint-disable-next-line no-console
        console.warn("[landing-loader]", result.errors);
      }

      if (result.canvasComponent && !canvasRef.current) {
        canvasRef.current = result.canvasComponent;
      }

      setProgress(100);
      setReady(true);
    };

    run();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  return {
    progress,
    ready,
    Canvas3D: canvasRef.current,
    errors,
  };
}

async function loadLandingAssets({
  signal,
  onProgress,
  onCanvasReady,
}: LoaderOptions): Promise<LoaderResult> {
  let completedWeight = 0;
  const errors: string[] = [];
  const weightByStatus: Record<LoadStatus, number> = {
    success: 1,
    skipped: 1,
    timeout: 0.6,
    error: 0.3,
    aborted: 0,
  };

  const pushProgress = () => {
    const value = Math.min(99, Math.round((completedWeight / TOTAL_WEIGHT) * 100));
    onProgress(value);
  };

  const register = (weight: number, status: LoadStatus, label: string) => {
    if (signal.aborted || status === "aborted") return;
    const multiplier = weightByStatus[status] ?? 0;
    if (multiplier > 0) {
      completedWeight = Math.min(TOTAL_WEIGHT, completedWeight + weight * multiplier);
      pushProgress();
    }
    if (status !== "success" && status !== "skipped") {
      errors.push(`${label}:${status}`);
    }
  };

  const perImageWeight = COIN_IMAGE_NAMES.length ? IMAGE_WEIGHT / COIN_IMAGE_NAMES.length : 0;

  await preloadCoinImages(signal, (status, name) =>
    register(perImageWeight, status, `image:${name}`)
  );

  if (!signal.aborted) {
    const fontStatus = await waitForFonts(signal);
    register(FONT_WEIGHT, fontStatus, "fonts");
  }

  let canvasComponent: CanvasComponent | null = null;
  if (!signal.aborted) {
    const moduleResult = await loadCanvasModule(signal);
    if (moduleResult.module) {
      canvasComponent = moduleResult.module;
      onCanvasReady?.(moduleResult.module);
    }
    register(MODULE_WEIGHT, moduleResult.status, "module:Canvas3D");
  }

  if (!signal.aborted) onProgress(100);

  return { canvasComponent, errors };
}

type ImageReport = (status: LoadStatus, name: string) => void;

async function preloadCoinImages(signal: AbortSignal, report: ImageReport) {
  const total = COIN_IMAGE_NAMES.length;
  if (!total) return;

  let index = 0;
  const workers = Array.from(
    { length: Math.min(IMAGE_CONCURRENCY, total) || 1 },
    async () => {
      while (!signal.aborted) {
        const current = index++;
        if (current >= total) return;
        const name = COIN_IMAGE_NAMES[current];
        const url = `/3D_crypto_coin/${name}`;
        const status = await preloadImage(url, signal, IMAGE_TIMEOUT_MS);
        report(status, name);
      }
    }
  );

  await Promise.all(workers);
}

async function preloadImage(
  url: string,
  signal: AbortSignal,
  timeoutMs: number
): Promise<LoadStatus> {
  if (signal.aborted) return "aborted";

  return new Promise<LoadStatus>((resolve) => {
    const img = new Image();
    img.decoding = "async";

    let settled = false;

    const cleanup = () => {
      img.onload = null;
      img.onerror = null;
      signal.removeEventListener("abort", abortHandler);
      window.clearTimeout(timer);
    };

    const finish = (status: LoadStatus) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve(status);
    };

    const abortHandler = () => finish("aborted");
    signal.addEventListener("abort", abortHandler, { once: true });

    const timer = window.setTimeout(() => finish("timeout"), timeoutMs);

    img.onload = () => finish("success");
    img.onerror = () => finish("error");

    img.src = url;
  });
}

async function waitForFonts(signal: AbortSignal): Promise<LoadStatus> {
  if (typeof document === "undefined" || !(document as any).fonts) return "skipped";
  if (signal.aborted) return "aborted";

  return new Promise<LoadStatus>((resolve) => {
    let settled = false;

    const cleanup = () => {
      signal.removeEventListener("abort", abortHandler);
      window.clearTimeout(timer);
    };

    const finish = (status: LoadStatus) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolve(status);
    };

    const abortHandler = () => finish("aborted");
    signal.addEventListener("abort", abortHandler, { once: true });

    const timer = window.setTimeout(() => finish("timeout"), FONT_TIMEOUT_MS);

    (document as any).fonts
      .ready
      .then(() => finish("success"))
      .catch(() => finish("error"));
  });
}

async function loadCanvasModule(
  signal: AbortSignal
): Promise<{ status: LoadStatus; module: CanvasComponent | null }> {
  if (signal.aborted) return { status: "aborted", module: null };

  try {
    const mod = await import("@/components/three/Canvas3D");
    if (signal.aborted) return { status: "aborted", module: null };
    return { status: "success", module: mod.default as CanvasComponent };
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error("[landing-loader] Canvas3D import failed", error);
    return { status: "error", module: null };
  }
}

