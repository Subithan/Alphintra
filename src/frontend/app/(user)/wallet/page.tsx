"use client";

import { useEffect, useState } from "react";
import GradientBorder from "@/components/ui/GradientBorder";
import {
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff,
  Key,
  RefreshCw,
  Wallet as WalletIcon,
} from "lucide-react";

type BinanceEnvironment = "production" | "testnet";

interface Balance {
  asset: string;
  free: string;
  locked: string;
}

const getErrorMessage = (error: unknown): string => {
  if (error instanceof Error && typeof error.message === "string") {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return "Unexpected error";
};

export default function Wallet() {
  const [apiKey, setApiKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [showSecret, setShowSecret] = useState(false);
  const [environment, setEnvironment] =
    useState<BinanceEnvironment>("production");
  const [isConnected, setIsConnected] = useState(false);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [maskedApiKey, setMaskedApiKey] = useState("");

  const persistEnvironment = (value: BinanceEnvironment) => {
    setEnvironment(value);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("walletConnectionEnv", value);
    }
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedEnv = window.localStorage.getItem("walletConnectionEnv");
      if (storedEnv === "production" || storedEnv === "testnet") {
        setEnvironment(storedEnv);
      }
      const storedMask = window.localStorage.getItem("walletMaskedApiKey");
      if (storedMask) {
        setMaskedApiKey(storedMask);
      }
    }

    const loadConnectionStatus = async () => {
      try {
        const response = await fetch("/api/binance/connection-status", {
          cache: "no-store",
        });

        if (response.ok) {
          const data = await response.json();

          if (data.connected) {
            setIsConnected(true);
            const inferredEnv =
              data.environment === "testnet" ? "testnet" : "production";
            persistEnvironment(inferredEnv);
            if (typeof window !== "undefined") {
              const storedMask =
                window.localStorage.getItem("walletMaskedApiKey");
              if (storedMask) {
                setMaskedApiKey(storedMask);
              }
            }
            await fetchBalances({ showToast: false });
          } else {
            setIsConnected(false);
            setMaskedApiKey("");
            setBalances([]);
          }
        } else if (response.status === 401) {
          setIsConnected(false);
          setMaskedApiKey("");
          setBalances([]);
        }
      } catch (err) {
        console.error("Failed to check connection status", err);
      } finally {
        setInitializing(false);
      }
    };

    loadConnectionStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchBalances = async ({
    showToast = true,
    manageLoading = true,
  }: { showToast?: boolean; manageLoading?: boolean } = {}) => {
    if (manageLoading) {
      setLoading(true);
    }
    setError("");

    try {
      const response = await fetch("/api/binance/balances", {
        cache: "no-store",
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const detail =
          body?.error ?? body?.detail ?? `Request failed with ${response.status}`;

        if (response.status === 401) {
          setIsConnected(false);
          setBalances([]);
        }

        throw new Error(detail);
      }

      const data = await response.json();
      setBalances(Array.isArray(data?.balances) ? data.balances : []);

      if (showToast) {
        setSuccess("Balances refreshed successfully!");
        setTimeout(() => setSuccess(""), 2000);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      if (manageLoading) {
        setLoading(false);
      }
    }
  };

  const connectToBinance = async () => {
    if (!apiKey || !secretKey) {
      setError("Please enter both API Key and Secret Key");
      setSuccess("");
      return;
    }

    if (apiKey.length !== 64) {
      setError("API Key must be exactly 64 characters long");
      setSuccess("");
      return;
    }

    if (secretKey.length !== 64) {
      setError("Secret Key must be exactly 64 characters long");
      setSuccess("");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch("/api/binance/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ apiKey, secretKey, environment }),
      });

      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detail =
          payload?.error ??
          payload?.detail ??
          `Request failed with ${response.status}`;
        throw new Error(detail);
      }

      const masked = apiKey.slice(-4);
      setMaskedApiKey(masked);
      if (typeof window !== "undefined") {
        window.localStorage.setItem("walletMaskedApiKey", masked);
      }

      const envFromResponse =
        payload?.environment === "testnet" ? "testnet" : environment;
      persistEnvironment(envFromResponse);

      setIsConnected(true);
      setSuccess(payload?.message ?? "Successfully connected to Binance!");
      setApiKey("");
      setSecretKey("");

      await fetchBalances({ showToast: false, manageLoading: false });
      setLoading(false);
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  };

  const disconnect = () => {
    setLoading(true);
    setError("");
    setSuccess("");

    fetch("/api/binance/disconnect", { method: "POST" })
      .then(async (response) => {
        const body = await response.json().catch(() => ({}));

        if (!response.ok) {
          const detail =
            body?.error ??
            body?.detail ??
            `Request failed with ${response.status}`;
          throw new Error(detail);
        }

        setIsConnected(false);
        setBalances([]);
        setMaskedApiKey("");
        if (typeof window !== "undefined") {
          window.localStorage.removeItem("walletMaskedApiKey");
        }

        const envFromResponse =
          body?.environment === "testnet" ? "testnet" : environment;
        persistEnvironment(envFromResponse);

        setSuccess(body?.message ?? "Disconnected from Binance");
        setTimeout(() => setSuccess(""), 2000);
      })
      .catch((err) => {
        setError(getErrorMessage(err));
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Wallet</h1>
            <p className="text-muted-foreground mt-1">
              Connect to Binance and view your balances
            </p>
          </div>
          {isConnected && (
            <button
              type="button"
              onClick={fetchBalances}
              disabled={loading || initializing}
              className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
              Refresh
            </button>
          )}
        </div>

        {initializing && (
          <div className="bg-muted/20 border border-muted/40 rounded-lg p-4 flex items-center gap-3 text-sm text-muted-foreground">
            <RefreshCw className="w-4 h-4 animate-spin" />
            Checking existing Binance connection...
          </div>
        )}

        {success && (
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 flex items-center gap-3 animate-in fade-in duration-300">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-green-400">{success}</span>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-center gap-3 animate-in fade-in duration-300">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {!isConnected ? (
          <GradientBorder gradientAngle="135deg" className="p-6">
            <div className="flex items-center gap-2 mb-6">
              <Key className="w-5 h-5 text-yellow-500" />
              <h3 className="text-xl font-semibold">Connect to Binance</h3>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Environment
                </label>
                <select
                  value={environment}
                  onChange={(event) =>
                    persistEnvironment(
                      event.target.value === "testnet" ? "testnet" : "production"
                    )
                  }
                  disabled={loading || initializing}
                  className="w-full p-3 bg-muted/20 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 text-sm"
                >
                  <option value="production">Production (Live Trading)</option>
                  <option value="testnet">Testnet (Sandbox)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Binance API Key
                </label>
                <input
                  type="text"
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                  placeholder="Enter your Binance API Key"
                  className="w-full p-3 bg-muted/20 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 font-mono text-sm"
                  maxLength={64}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Binance Secret Key
                  <span className="text-xs text-muted-foreground ml-2">
                    (Must be 64 characters)
                  </span>
                </label>
                <div className="relative">
                  <input
                    type={showSecret ? "text" : "password"}
                    value={secretKey}
                    onChange={(event) => setSecretKey(event.target.value)}
                    placeholder="Enter your Binance Secret Key"
                    className="w-full p-3 bg-muted/20 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 pr-12 font-mono text-sm"
                    maxLength={64}
                  />
                  <button
                    type="button"
                    onClick={() => setShowSecret((prev) => !prev)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showSecret ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
                <h4 className="font-semibold text-amber-400 mb-2">
                  Security Notice:
                </h4>
                <ul className="text-sm text-amber-300 space-y-1">
                  <li>• Only use API keys with &quot;Read&quot; permissions</li>
                  <li>• Never share your secret key with anyone</li>
                  <li>• Keys are encrypted and stored securely</li>
                </ul>
              </div>

              <button
                type="button"
                onClick={connectToBinance}
                disabled={loading || initializing || !apiKey || !secretKey}
                className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-semibold py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  "Connect to Binance"
                )}
              </button>
            </div>
          </GradientBorder>
        ) : (
          <div className="space-y-6">
            <GradientBorder gradientAngle="135deg" className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-semibold text-green-400">
                    Connected to Binance
                  </span>
                  <p className="text-sm text-muted-foreground mt-1">
                    API Key: ****{maskedApiKey || "****"} • Environment:{" "}
                    {environment === "testnet" ? "Testnet" : "Production"}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={disconnect}
                  disabled={loading}
                  className="text-red-400 hover:text-red-300 disabled:opacity-60 disabled:cursor-not-allowed text-sm font-medium transition-colors"
                >
                  Disconnect
                </button>
              </div>
            </GradientBorder>

            <GradientBorder gradientAngle="225deg" className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <WalletIcon className="w-5 h-5 text-green-500" />
                <h3 className="text-xl font-semibold">Your Binance Balances</h3>
              </div>

              {loading ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-yellow-500" />
                  <p className="text-muted-foreground">Loading balances...</p>
                </div>
              ) : balances.length > 0 ? (
                <div className="space-y-3">
                  {balances.map((balance) => (
                    <div
                      key={balance.asset}
                      className="flex items-center justify-between p-4 bg-muted/20 rounded-lg hover:bg-muted/30 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-yellow-500/20 rounded-full flex items-center justify-center">
                          <span className="font-bold text-yellow-400 text-sm">
                            {balance.asset.slice(0, 2)}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium text-lg">
                            {balance.asset}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Available: {parseFloat(balance.free).toFixed(8)}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-lg">
                          {(
                            parseFloat(balance.free) +
                            parseFloat(balance.locked)
                          ).toFixed(8)}
                        </div>
                        {parseFloat(balance.locked) > 0 && (
                          <div className="text-sm text-orange-400">
                            Locked: {parseFloat(balance.locked).toFixed(8)}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <WalletIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No balances found</p>
                  <button
                    type="button"
                    onClick={fetchBalances}
                    className="mt-4 text-blue-400 hover:text-blue-300 text-sm"
                  >
                    Click to load balances
                  </button>
                </div>
              )}
            </GradientBorder>
          </div>
        )}
      </div>
    </div>
  );
}
