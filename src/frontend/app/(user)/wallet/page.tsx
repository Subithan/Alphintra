"use client";

import { useState, useEffect } from "react";
import GradientBorder from "@/components/ui/GradientBorder";
import {
  Eye,
  EyeOff,
  Key,
  RefreshCw,
  Wallet as WalletIcon,
  AlertCircle,
  CheckCircle,
} from "lucide-react";

interface Balance {
  asset: string;
  free: string;
  locked: string;
}

// Mock balance data for demonstration
const MOCK_BALANCES: Balance[] = [
  { asset: "BTC", free: "0.05234", locked: "0.00000" },
  { asset: "ETH", free: "1.23456", locked: "0.10000" },
  { asset: "USDT", free: "1500.00000", locked: "0.00000" },
  { asset: "BNB", free: "5.67890", locked: "0.50000" },
];

export default function Wallet() {
  const [apiKey, setApiKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [showSecret, setShowSecret] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [maskedApiKey, setMaskedApiKey] = useState("");

  // Check if already connected on page load
  useEffect(() => {
    checkMockConnection();
  }, []);

  const checkMockConnection = () => {
    const storedApiKey = localStorage.getItem('mockBinanceApiKey');
    const storedConnected = localStorage.getItem('mockBinanceConnected');

    if (storedConnected === 'true' && storedApiKey) {
      setIsConnected(true);
      setMaskedApiKey(storedApiKey);
      // Load mock balances after a short delay to simulate fetching
      setTimeout(() => {
        setBalances(MOCK_BALANCES);
      }, 500);
    }
  };

  const connectToBinance = async () => {
    if (!apiKey || !secretKey) {
      setError("Please enter both API Key and Secret Key");
      setSuccess("");
      return;
    }

    // Validate key lengths (64 characters each)
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

    // Simulate API call delay for realistic feel
    setTimeout(() => {
      // Mock successful connection
      const masked = apiKey.slice(-4);
      setMaskedApiKey(masked);
      setIsConnected(true);
      setSuccess("Successfully connected to Binance!");

      // Store in localStorage for persistence
      localStorage.setItem('mockBinanceConnected', 'true');
      localStorage.setItem('mockBinanceApiKey', masked);

      // Clear form inputs
      setApiKey("");
      setSecretKey("");

      // Load mock balances after connection
      setTimeout(() => {
        setBalances(MOCK_BALANCES);
        setLoading(false);
        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(""), 3000);
      }, 800);
    }, 1200); // 1.2 second delay to simulate network request
  };

  const fetchBalances = async () => {
    setLoading(true);
    setError("");

    // Simulate fetching delay
    setTimeout(() => {
      setBalances(MOCK_BALANCES);
      setLoading(false);
      setSuccess("Balances refreshed successfully!");
      setTimeout(() => setSuccess(""), 2000);
    }, 600);
  };

  const disconnect = () => {
    // Clear all states
    setIsConnected(false);
    setBalances([]);
    setMaskedApiKey("");
    setApiKey("");
    setSecretKey("");
    setError("");
    setSuccess("");

    // Clear from localStorage
    localStorage.removeItem('mockBinanceConnected');
    localStorage.removeItem('mockBinanceApiKey');

    setSuccess("Disconnected from Binance");
    setTimeout(() => setSuccess(""), 2000);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="space-y-6">
        {/* Page Header */}
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
              disabled={loading}
              className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
              Refresh
            </button>
          )}
        </div>

        {/* Success Message */}
        {success && (
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 flex items-center gap-3 animate-in fade-in duration-300">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-green-400">{success}</span>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-center gap-3 animate-in fade-in duration-300">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {!isConnected ? (
          /* Binance Connection Form */
          <GradientBorder gradientAngle="135deg" className="p-6">
            <div className="flex items-center gap-2 mb-6">
              <Key className="w-5 h-5 text-yellow-500" />
              <h3 className="text-xl font-semibold">Connect to Binance</h3>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Binance API Key
                  {/* <span className="text-xs text-muted-foreground ml-2">
                    (Must be 64 characters)
                  </span> */}
                </label>
                <input
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your Binance API Key"
                  className="w-full p-3 bg-muted/20 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 font-mono text-sm"
                  maxLength={64}
                />
                {/* <div className="text-xs text-muted-foreground mt-1">
                  Length: {apiKey.length}/64 characters
                </div> */}
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
                    onChange={(e) => setSecretKey(e.target.value)}
                    placeholder="Enter your Binance Secret Key"
                    className="w-full p-3 bg-muted/20 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 pr-12 font-mono text-sm"
                    maxLength={64}
                  />
                  <button
                    type="button"
                    onClick={() => setShowSecret(!showSecret)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showSecret ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                {/* <div className="text-xs text-muted-foreground mt-1">
                  Length: {secretKey.length}/64 characters
                </div> */}
              </div>

              <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
                <h4 className="font-semibold text-amber-400 mb-2">
                  Security Notice:
                </h4>
                <ul className="text-sm text-amber-300 space-y-1">
                  <li>• Only use API keys with &quot;Read&quot; permissions</li>
                  <li>• Never share your secret key with anyone</li>
                  <li>• Keys are encrypted and stored securely</li>
                  <li>• Demo mode: Enter any 64-character keys to connect</li>
                </ul>
              </div>

              <button
                type="button"
                onClick={connectToBinance}
                disabled={loading || !apiKey || !secretKey}
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
          /* Balance Display */
          <div className="space-y-6">
            {/* Connection Status */}
            {isConnected && (
              <GradientBorder gradientAngle="135deg" className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    <div>
                      <span className="font-semibold text-green-400">
                        Connected to Binance
                      </span>
                      <p className="text-sm text-muted-foreground">
                        API Key: ****{maskedApiKey || '****'} • Status: Active
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={disconnect}
                    className="text-red-400 hover:text-red-300 text-sm font-medium transition-colors"
                  >
                    Disconnect
                  </button>
                </div>
              </GradientBorder>
            )}

            {/* Balances */}
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
                          <div className="font-medium text-lg">{balance.asset}</div>
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
                  <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                    <p className="text-sm text-blue-400 text-center">
                      💡 Demo Mode: Displaying mock balance data for demonstration
                    </p>
                  </div>
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
