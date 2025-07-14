"use client";

import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import BalanceCard from "@/components/ui/dashboard/BalanceCard";
import CryptoTable from "@/components/ui/dashboard/cryptoTable";
import NewsCard from "@/components/ui/dashboard/newsCard";
import PriceChart from "@/components/ui/dashboard/PriceChart";
import GradientBorder from '@/components/ui/GradientBorder';
import { MoreHorizontal } from 'lucide-react';

export default function Dashboard() {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true); // ensures client-side rendering only
  }, []);

  if (!mounted) return null; // prevent rendering until after hydration

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 overflow-x-hidden">
        <div className="col-span-5 lg:col-start-1 lg:col-end-4 flex flex-col gap-8">
          <GradientBorder gradientAngle="275deg" className="p-5">
            <BalanceCard />
          </GradientBorder>
          <GradientBorder gradientAngle="275deg" className="p-5">
            <CryptoTable />
          </GradientBorder>
        </div>
        <div className="col-span-5 lg:col-start-4 lg:col-end-6 flex flex-col gap-8">
          <GradientBorder gradientAngle="315deg" className="p-5">
            <div className="flex justify-between items-center mb-4">
              <h2
                className="text-xl font-bold"
                style={{
                  color: resolvedTheme === "dark" ? "white" : "black",
                }}
              >
                BREAKING NEWS
              </h2>
              <div
                className={`text-gray-400 hover:${
                  resolvedTheme === "dark" ? "text-white" : "text-black"
                } cursor-pointer`}
              >
                <MoreHorizontal className="w-6 h-6" />
              </div>
            </div>
            <NewsCard />
          </GradientBorder>
          <GradientBorder gradientAngle="315deg" className="p-5">
            <PriceChart />
          </GradientBorder>
        </div>
      </div>
    </div>
  );
}
