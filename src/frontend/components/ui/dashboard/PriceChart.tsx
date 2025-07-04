// app/ui/dashboard/PriceChart.tsx
"use client"

import React from 'react';
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

interface PriceChartProps {
  price: number;
}

export default function PriceChart({ price }: PriceChartProps) {
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
    <Card
      className="p-0 rounded-lg shadow-lg text-white"
      style={{ backgroundColor: '#060819', border: '#060819' }}
    >
      <CardHeader className="flex justify-between items-center mb-2 px-2 pt-2 pb-0">
        <CardTitle className="text-xl font-bold">BITCOIN</CardTitle>
        <div className="text-gray-400 hover:text-white cursor-pointer">
          {price.toLocaleString()}
        </div>
      </CardHeader>
      <CardContent className="px-2 pt-0 pb-0">
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
      </CardContent>
    </Card>
  );
}