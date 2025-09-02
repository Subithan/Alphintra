"use client";

import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import GradientBorder from '@/components/ui/GradientBorder';
import { Plus, Plug, ShoppingCart, User } from 'lucide-react';
import { useRouter } from "next/navigation";

export default function Strategy() {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const handlePluginClick = (strategyName: string) => {
    console.log(`Activating plugin for strategy: ${strategyName}`);
    // Add your plugin activation logic here
  };

  const handleCreateStrategy = () => {
    console.log("Creating new strategy...");
    router.push("/strategy-hub"); // Add this navigation
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Strategy Hub</h1>
            <p className="text-muted-foreground mt-1">Manage your trading strategies</p>
          </div>
          <button 
            onClick={handleCreateStrategy}
            className="flex items-center gap-2 bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Strategy
          </button>
        </div>

        {/* My Created Strategies */}
        <GradientBorder gradientAngle="135deg" className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <User className="w-5 h-5 text-blue-500" />
            <h3 className="text-xl font-semibold">My Created Strategies</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <div>
                  <div className="font-medium">Bitcoin DCA Strategy</div>
                  <div className="text-sm text-muted-foreground">Dollar Cost Averaging • Created by you</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-green-500 font-semibold">+12.5%</span>
                <button 
                  onClick={() => handlePluginClick("Bitcoin DCA Strategy")}
                  className="flex items-center gap-1 bg-yellow-500 hover:bg-yellow-600 text-black px-3 py-1 rounded-md text-sm transition-colors"
                >
                  <Plug className="w-3 h-3" />
                  Plugin
                </button>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <div>
                  <div className="font-medium">Custom Grid Trading</div>
                  <div className="text-sm text-muted-foreground">Advanced Grid Algorithm • Created by you</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-green-500 font-semibold">+8.3%</span>
                <button 
                  onClick={() => handlePluginClick("Custom Grid Trading")}
                  className="flex items-center gap-1 bg-yellow-500 hover:bg-yellow-600 text-black px-3 py-1 rounded-md text-sm transition-colors"
                >
                  <Plug className="w-3 h-3" />
                  Plugin
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                <div>
                  <div className="font-medium">ML Momentum Strategy</div>
                  <div className="text-sm text-muted-foreground">Machine Learning Based • Created by you</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-red-500 font-semibold">-2.1%</span>
                <button 
                  onClick={() => handlePluginClick("ML Momentum Strategy")}
                  className="flex items-center gap-1 bg-yellow-500 hover:bg-yellow-600 text-black px-3 py-1 rounded-md text-sm transition-colors"
                >
                  <Plug className="w-3 h-3" />
                  Plugin
                </button>
              </div>
            </div>
          </div>
        </GradientBorder>

        {/* Bought Strategies */}
        <GradientBorder gradientAngle="225deg" className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <ShoppingCart className="w-5 h-5 text-green-500" />
            <h3 className="text-xl font-semibold">Bought Strategies</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                <div>
                  <div className="font-medium">Professional Scalping Bot</div>
                  <div className="text-sm text-muted-foreground">High-frequency trading • By @TradingPro</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-green-500 font-semibold">+18.7%</span>
                <button 
                  onClick={() => handlePluginClick("Professional Scalping Bot")}
                  className="flex items-center gap-1 bg-yellow-500 hover:bg-yellow-600 text-black px-3 py-1 rounded-md text-sm transition-colors"
                >
                  <Plug className="w-3 h-3" />
                  Plugin
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                <div>
                  <div className="font-medium">Arbitrage Master</div>
                  <div className="text-sm text-muted-foreground">Cross-exchange arbitrage • By @ArbitrageKing</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-green-500 font-semibold">+15.2%</span>
                <button 
                  onClick={() => handlePluginClick("Arbitrage Master")}
                  className="flex items-center gap-1 bg-yellow-500 hover:bg-yellow-600 text-black px-3 py-1 rounded-md text-sm transition-colors"
                >
                  <Plug className="w-3 h-3" />
                  Plugin
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-3 h-3 bg-pink-500 rounded-full"></div>
                <div>
                  <div className="font-medium">AI Sentiment Trader</div>
                  <div className="text-sm text-muted-foreground">News sentiment analysis • By @AITrader</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-green-500 font-semibold">+22.4%</span>
                <button 
                  onClick={() => handlePluginClick("AI Sentiment Trader")}
                  className="flex items-center gap-1 bg-yellow-500 hover:bg-yellow-600 text-black px-3 py-1 rounded-md text-sm transition-colors"
                >
                  <Plug className="w-3 h-3" />
                  Plugin
                </button>
              </div>
            </div>
          </div>
        </GradientBorder>
      </div>
    </div>
  );
}