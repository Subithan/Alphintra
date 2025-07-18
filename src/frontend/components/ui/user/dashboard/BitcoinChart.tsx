"use client";

import React, { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useTheme } from "next-themes";

export default function BitcoinAreaChart({ days = 365 }: { days?: number }) {
  const [data, setData] = useState<{ time: string; price: number }[]>([]);
  const { theme } = useTheme();

  useEffect(() => {
    fetch(
      `https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=${days}`
    )
      .then((res) => res.json())
      .then((data) => {
        const prices = data.prices.map(
          ([timestamp, price]: [number, number]) => ({
            time: new Date(timestamp).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            }),
            price: Number(price.toFixed(2)),
          })
        );
        setData(prices);
      })
      .catch((err) => console.error("Failed to fetch Bitcoin data:", err));
  }, [days]);

  // Define stroke colors for dark/light
  const axisColor = theme === "dark" ? "#020817" : "#ffffff";

  return (
    <div className="w-full h-[180px]">
      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <XAxis dataKey="time"  tick={{ fontSize: 10 }} hide/>
            <YAxis stroke={axisColor}   tick={{ fontSize: 10 }} />
            <Tooltip />
            <Area
              type="monotone"
              dataKey="price"
              stroke="#d4af37"
              fill="rgba(212, 175, 55, 0.3)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      ) : (
        <p className="text-center text-muted">Loading...</p>
      )}
    </div>
  );
}
