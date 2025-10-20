"use client";

import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import GradientBorder from '@/components/ui/GradientBorder';
import { Plus, Plug, ShoppingCart, User } from 'lucide-react';
import { useRouter } from "next/navigation";
import { fetchMyStrategies, MyStrategySummary } from "@/lib/api/myStrategies";
import { fetchOrdersForCurrentUser, PurchasedStrategy } from "@/app/api/ordersApi";

export default function Strategy() {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [myStrategies, setMyStrategies] = useState<MyStrategySummary[]>([]);
  const [loadingStrategies, setLoadingStrategies] = useState(true);
  const [strategiesError, setStrategiesError] = useState<string | null>(null);
  const [boughtStrategies, setBoughtStrategies] = useState<PurchasedStrategy[]>([]);
  const [loadingBought, setLoadingBought] = useState(true);
  const [boughtError, setBoughtError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
  }, []);

  const handlePluginClick = (strategyName: string) => {
    console.log(`Activating plugin for strategy: ${strategyName}`);
    // Add your plugin activation logic here
  };

  const handleCreateStrategy = () => {
    console.log("Creating new strategy...");
    router.push("/strategy-hub"); // Add this navigation
  };

  useEffect(() => {
    if (!mounted) return;

    setLoadingStrategies(true);
    fetchMyStrategies()
      .then((data) => {
        setMyStrategies(data);
        setStrategiesError(null);
      })
      .catch((err) => {
        console.error("Failed to load strategies", err);
        setStrategiesError(err.message ?? "Failed to load strategies");
      })
      .finally(() => setLoadingStrategies(false));
  }, [mounted]);

  useEffect(() => {
    if (!mounted) return;

    setLoadingBought(true);
    fetchOrdersForCurrentUser()
      .then((orders) => {
        setBoughtStrategies(orders);
        setBoughtError(null);
      })
      .catch((err) => {
        console.error("Failed to load purchased strategies", err);
        setBoughtError(err.message ?? "Failed to load purchased strategies");
      })
      .finally(() => setLoadingBought(false));
  }, [mounted]);

  if (!mounted) return null;

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
          {loadingStrategies ? (
            <p className="text-sm text-muted-foreground">Loading strategies...</p>
          ) : strategiesError ? (
            <p className="text-sm text-red-500">{strategiesError}</p>
          ) : myStrategies.length === 0 ? (
            <p className="text-sm text-muted-foreground">You haven&apos;t created any strategies yet.</p>
          ) : (
            <div className="space-y-3">
              {myStrategies.map((strategy) => (
                <div
                  key={strategy.workflow_uuid}
                  className="flex items-center justify-between p-4 bg-muted/20 rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-3 h-3 bg-green-500 rounded-full" />
                    <div>
                      <div className="font-medium">{strategy.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {strategy.code_metrics.lines} lines •{" "}
                        {strategy.compiler_version}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handlePluginClick(strategy.name)}
                      className="flex items-center gap-1 bg-yellow-500 hover:bg-yellow-600 text-black px-3 py-1 rounded-md text-sm transition-colors"
                    >
                      <Plug className="w-3 h-3" />
                      Plugin
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GradientBorder>

        {/* Bought Strategies */}
        <GradientBorder gradientAngle="225deg" className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <ShoppingCart className="w-5 h-5 text-green-500" />
            <h3 className="text-xl font-semibold">Bought Strategies</h3>
          </div>
          {loadingBought ? (
            <p className="text-sm text-muted-foreground">Loading purchases...</p>
          ) : boughtError ? (
            <p className="text-sm text-red-500">{boughtError}</p>
          ) : boughtStrategies.length === 0 ? (
            <p className="text-sm text-muted-foreground">You haven&apos;t purchased any strategies yet.</p>
          ) : (
            <div className="space-y-3">
              {boughtStrategies.map((purchase) => {
                const price =
                  purchase.strategy.priceCents === 0
                    ? 'Free'
                    : `$${(purchase.strategy.priceCents / 100).toFixed(2)}`;
                return (
                  <div
                    key={purchase.orderId}
                    className="flex items-center justify-between p-4 bg-muted/20 rounded-lg"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                      <div>
                        <div className="font-medium">
                          {purchase.strategy.name}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Order #{purchase.orderId} • {purchase.status}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {price} • Subscribers: {purchase.strategy.subscriberCount}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() =>
                          handlePluginClick(purchase.strategy.name)
                        }
                        className="flex items-center gap-1 bg-yellow-500 hover:bg-yellow-600 text-black px-3 py-1 rounded-md text-sm transition-colors"
                      >
                        <Plug className="w-3 h-3" />
                        Plugin
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </GradientBorder>
      </div>
    </div>
  );
}
