"use client";

import { useState, useEffect } from "react";
import GradientBorder from '@/components/ui/GradientBorder';
import { Eye, EyeOff, Key, RefreshCw, Wallet as WalletIcon, AlertCircle } from 'lucide-react';

interface Balance {
  asset: string;
  free: string;
  locked: string;
}

export default function Wallet() {
  const [apiKey, setApiKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [showSecret, setShowSecret] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Check if already connected on page load
  useEffect(() => {
    checkConnection();
  }, []);

  // ...existing code...

const checkConnection = async () => {
  try {
    const res = await fetch('http://localhost:8011/binance/connection-status');
    const text = await res.text();
    let data: any = {};
    try { data = JSON.parse(text); } catch { data = { detail: text }; }
    setIsConnected(!!data.connected);
    if (data.connected) {
      fetchBalances();
    }
  } catch (err) {
    console.error('Failed to check connection:', err);
  }
};

const connectToBinance = async () => {
  if (!apiKey || !secretKey) {
    setError('Please enter both API Key and Secret Key');
    return;
  }

  setLoading(true);
  setError('');
  console.log('DEBUG: connectToBinance started');

  try {
    const response = await fetch('http://localhost:8011/binance/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ apiKey, secretKey }),
    });

    const text = await response.text();
    let data: any = {};
    try { data = JSON.parse(text); } catch { data = { detail: text }; }
    console.log('DEBUG: connect response', response.status, data);

    if (response.ok) {
      setIsConnected(true);
      fetchBalances();
      setApiKey('');
      setSecretKey('');
    } else {
      setError(data.detail || data.message || data.error || 'Failed to connect to Binance');
    }
  } catch (err) {
    console.error('DEBUG: connectToBinance error', err);
    setError('Network error. Please try again.');
  } finally {
    console.log('DEBUG: connectToBinance finally - clearing loading');
    setLoading(false);
  }
};

const fetchBalances = async () => {
  setLoading(true);
  try {
    const response = await fetch('http://localhost:8011/binance/balances');
    const text = await response.text();
    let data: any = {};
    try { data = JSON.parse(text); } catch { data = { detail: text }; }

    if (response.ok && Array.isArray(data.balances)) {
      const nonZeroBalances = data.balances.filter(
        (balance: Balance) => parseFloat(balance.free) > 0 || parseFloat(balance.locked) > 0
      );
      setBalances(nonZeroBalances);
    } else {
      setError(data.detail || data.message || data.error || 'Failed to fetch balances');
    }
  } catch (err) {
    setError('Failed to fetch balances');
  } finally {
    setLoading(false);
  }
};

// ...existing code...

  const disconnect = async () => {
    try {
      await fetch('http://localhost:8011/binance/disconnect', { method: 'POST' });
      setIsConnected(false);
      setBalances([]);
    } catch (err) {
      console.error('Failed to disconnect:', err);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Wallet</h1>
            <p className="text-muted-foreground mt-1">Connect to Binance and view your balances</p>
          </div>
          {isConnected && (
            <button
              onClick={fetchBalances}
              disabled={loading}
              className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-center gap-3">
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
                </label>
                <input
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your Binance API Key"
                  className="w-full p-3 bg-muted/20 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Binance Secret Key
                </label>
                <div className="relative">
                  <input
                    type={showSecret ? "text" : "password"}
                    value={secretKey}
                    onChange={(e) => setSecretKey(e.target.value)}
                    placeholder="Enter your Binance Secret Key"
                    className="w-full p-3 bg-muted/20 border border-muted rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 pr-12"
                  />
                  <button
                    type="button"
                    onClick={() => setShowSecret(!showSecret)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showSecret ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
                <h4 className="font-semibold text-amber-400 mb-2">Security Notice:</h4>
                <ul className="text-sm text-amber-300 space-y-1">
                  <li>• Only use API keys with "Read" permissions</li>
                  <li>• Never share your secret key</li>
                  <li>• Keys are encrypted and stored securely</li>
                </ul>
              </div>

              <button
                onClick={connectToBinance}
                disabled={loading || !apiKey || !secretKey}
                className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-semibold py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Connecting...' : 'Connect to Binance'}
              </button>
            </div>
          </GradientBorder>
        ) : (
          /* Balance Display */
          <div className="space-y-6">
            {/* Connection Status */}
            <GradientBorder gradientAngle="135deg" className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="font-semibold">Connected to Binance</span>
                </div>
                <button
                  onClick={disconnect}
                  className="text-red-400 hover:text-red-300 text-sm"
                >
                  Disconnect
                </button>
              </div>
            </GradientBorder>

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
                      className="flex items-center justify-between p-4 bg-muted/20 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-yellow-500/20 rounded-full flex items-center justify-center">
                          <span className="font-bold text-yellow-400 text-sm">
                            {balance.asset.slice(0, 2)}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium">{balance.asset}</div>
                          <div className="text-sm text-muted-foreground">
                            Available: {parseFloat(balance.free).toFixed(8)}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">
                          {(parseFloat(balance.free) + parseFloat(balance.locked)).toFixed(8)}
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
                </div>
              )}
            </GradientBorder>
          </div>
        )}
      </div>
    </div>
  );
}
