"use client"

import React, { useState, useEffect } from "react";
import { useTheme } from 'next-themes';
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
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  if (!mounted) return null;
  const currentTheme = theme === 'system' ? systemTheme : theme;

  return (
    <div className={`p-4 rounded-lg ${currentTheme === 'dark' ? 'bg-[#0a0a1a] border border-yellow-500/20 hover:bg-[#141426] text-white' : 'bg-gray-50 border border-gray-200 hover:bg-gray-100 text-gray-900'} flex flex-col transition-all`}>
      {/* Tabs */}
      <div className={`flex gap-4 mb-4 border-b ${currentTheme === 'dark' ? 'border-[#1a1a2e]' : 'border-gray-200'}`}>
        {tabs.map((tab) => (
          <button
            key={tab}
            className={cn(
              "pb-2 text-sm font-semibold transition",
              tab === activeTab
                ? `${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} border-b-2 border-yellow-500`
                : `${currentTheme === 'dark' ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`
            )}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className={`overflow-x-auto rounded-lg ${currentTheme === 'dark' ? 'bg-[#0a0a1a] border border-yellow-500/20 shadow-[0_0_0_1px_rgba(234,179,8,0.1)]' : 'bg-gray-50 border border-gray-200'}`}>
        <table className="min-w-full text-sm text-left">
          <thead className={`${currentTheme === 'dark' ? 'bg-[#101020] text-gray-500' : 'bg-gray-100 text-gray-600'} uppercase text-xs`}>
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
                className={`border-b ${currentTheme === 'dark' ? 'border-[#1f1f38] hover:bg-[#141426]' : 'border-gray-200 hover:bg-gray-100'} transition-colors`}
              >
                <td className="px-4 py-3 font-bold flex items-center gap-2">
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  <span className="text-lg">{row.icon}</span>
                  <span>{row.ticker}</span>
                </td>
                <td className="px-4 py-3">{row.expiry}</td>
                <td className="px-4 py-3">
                  <span className={`${currentTheme === 'dark' ? 'bg-[#1e1e3f] text-white' : 'bg-yellow-100 text-yellow-800'} px-3 py-1 rounded-full`}>
                    {row.type}
                  </span>
                </td>
                <td className="px-4 py-3">{row.strike}</td>
                <td className="px-4 py-3 flex flex-wrap gap-2">
                  {row.sector.map((sec, idx) => (
                    <span
                      key={idx}
                      className={`${currentTheme === 'dark' ? 'bg-[#1e1e3f] text-gray-300' : 'bg-gray-200 text-gray-700'} px-2 py-1 rounded-full text-xs`}
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
      <div className={`flex justify-center mt-4 ${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'} gap-1`}>
        <button className={`px-2 py-1 ${currentTheme === 'dark' ? 'hover:text-white' : 'hover:text-gray-900'} transition-colors`}>&lt;</button>
        {[1, 2, 3, 4].map((num) => (
          <button
            key={num}
            className={cn(
              "w-8 h-8 rounded-full transition-colors",
              num === 2
                ? `bg-yellow-500 ${currentTheme === 'dark' ? 'text-black' : 'text-black'}`
                : `${currentTheme === 'dark' ? 'hover:text-yellow-400' : 'hover:text-gray-900'}`
            )}
          >
            {num}
          </button>
        ))}
        <span className="px-2">...</span>
        <button className={`px-2 py-1 ${currentTheme === 'dark' ? 'hover:text-white' : 'hover:text-gray-900'} transition-colors`}>120</button>
        <button className={`px-2 py-1 ${currentTheme === 'dark' ? 'hover:text-white' : 'hover:text-gray-900'} transition-colors`}>&gt;</button>
      </div>
    </div>
  );
}