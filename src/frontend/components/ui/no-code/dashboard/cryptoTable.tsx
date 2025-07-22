"use client"

import React, { useState } from "react";
import { cn } from "@/lib/utils";

const tabs = ["Titans", "Momentum", "Macro", "Small"];

const data = [
  {
    ticker: "BTC",
    expiry: "28 apr",
    type: "Call",
    strike: "01,3C",
    sector: ["All", "SoL", "AI"],
    icon: "🟠",
  },
  {
    ticker: "ETH",
    expiry: "31 may",
    type: "Call",
    strike: "01,7ut",
    sector: ["All", "Solar", "SC"],
    icon: "⚪️",
  },
  {
    ticker: "STC",
    expiry: "31 may",
    type: "Put",
    strike: "Neutral",
    sector: ["DeFi", "Del", "Ice"],
    icon: "🔵",
  },
  // Add more as needed...
];

export default function CryptoTable() {
  const [activeTab, setActiveTab] = useState("Titans");

  return (
    <div className="text-white p-4">
      {/* Tabs */}
      <div className="flex gap-4 mb-4 border-b border-[#1a1a2e]">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={cn(
              "pb-2 text-sm font-semibold transition",
              tab === activeTab
                ? "text-white border-b-2 border-blue-500"
                : "text-gray-400 hover:text-white"
            )}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg bg-[#0a0a1a]">
        <table className="min-w-full text-sm text-left">
          <thead className="bg-[#101020] text-gray-400 uppercase text-xs">
            <tr>
              <th className="px-4 py-3">Ticker</th>
              <th className="px-4 py-3">Expiry</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Strike</th>
              <th className="px-4 py-3">Sector</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr
                key={i}
                className="border-b border-[#1a1a2e] hover:bg-[#141426]"
              >
                <td className="px-4 py-3 font-bold flex items-center gap-2">
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  <span className="text-lg">{row.icon}</span>
                  <span>{row.ticker}</span>
                </td>
                <td className="px-4 py-3">{row.expiry}</td>
                <td className="px-4 py-3">
                  <span className="bg-[#1e1e3f] text-white px-3 py-1 rounded-full">
                    {row.type}
                  </span>
                </td>
                <td className="px-4 py-3">{row.strike}</td>
                <td className="px-4 py-3 flex flex-wrap gap-2">
                  {row.sector.map((sec, idx) => (
                    <span
                      key={idx}
                      className="bg-[#1e1e3f] text-gray-300 px-2 py-1 rounded-full text-xs"
                    >
                      {sec}
                    </span>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-center mt-4 text-gray-400 gap-1">
        <button className="px-2 py-1 hover:text-white">&lt;</button>
        {[1, 2, 3, 4].map((num) => (
          <button
            key={num}
            className={cn(
              "w-8 h-8 rounded-full",
              num === 2
                ? "bg-blue-600 text-white"
                : "hover:text-white"
            )}
          >
            {num}
          </button>
        ))}
        <span className="px-2">...</span>
        <button className="px-2 py-1 hover:text-white">120</button>
        <button className="px-2 py-1 hover:text-white">&gt;</button>
      </div>
    </div>
  );
}