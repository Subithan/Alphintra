"use client"

import React, { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid } from "recharts";
import { BarChart3 } from "lucide-react";

interface PriceChartProps {
  price: number;
}

export default function PriceChart({ price }: PriceChartProps) {
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  if (!mounted) return null;
  const currentTheme = theme === 'system' ? systemTheme : theme;
  const chartData = [
    { x: 1, y: 31000 },
    { x: 2, y: 21100 },
    { x: 3, y: 9950 },
    { x: 4, y: 31200 },
    { x: 5, y: 21300 },
    { x: 6, y: 11250 },
    { x: 7, y: 7928 },
  ];

  const chartConfig = {
    price: {
      label: "Bitcoin Price",
      color: "#eab308",
    },
  };

  return (
    <div className={`p-4 rounded-lg ${currentTheme === 'dark' ? 'bg-[#0a0a1a] border border-yellow-500/20 hover:bg-[#141426] text-white' : 'bg-gray-50 border border-gray-200 hover:bg-gray-100 text-gray-900'} flex flex-col transition-all`}>
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-orange-500/10">
            <BarChart3 className="w-5 h-5 text-orange-500" />
          </div>
          <h2 className={`text-xl font-bold ${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}`}>BITCOIN</h2>
        </div>
        <div className={`text-lg font-semibold ${currentTheme === 'dark' ? 'text-slate-300' : 'text-gray-700'}`}>
          ${price.toLocaleString()}
        </div>
      </div>
      <div className="mt-4">
        <ChartContainer config={chartConfig} className="h-[180px] w-full">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="fillPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="2%" stopColor="#eab308" stopOpacity={0.5} />
                <stop offset="45%" stopColor="#eab308" stopOpacity={0} />
              </linearGradient>
            </defs>
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent indicator="dot" />}
            />
            <Area
              dataKey="y"
              type="natural"
              fill="url(#fillPrice)"
              stroke="#eab308"
            />
          </AreaChart>
        </ChartContainer>
      </div>
    </div>
  );
}