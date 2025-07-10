"use client";

import React, { useState } from "react";
import clsx from "clsx";

const exchangeRates = {
  USDT: 1.0,
  BTC: 62600.0,
  ETH: 3460.0,
};

const balances = {
  USDT: 253.75,
  BTC: 0.0051,
  ETH: 0.32,
};

type Props = {
  className?: string;
};

export default function BalanceCard({ className }: Props) {
  const [selectedCoin, setSelectedCoin] = useState<"USDT" | "BTC" | "ETH">("USDT");

  const balance = balances[selectedCoin];
  const usdValue = balance * exchangeRates[selectedCoin];

  return (
    <div
      className={clsx(
        "rounded-lg p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4",
        className
      )}
    >
      {/* Balance Info */}
      <div className="w-full">
        <div className="text-xl font-bold">Estimated Balance</div>
        <div className="text-2xl font-bold flex items-center gap-2 mt-1">
          {balance.toFixed(4)}
          <select
            value={selectedCoin}
            onChange={(e) => setSelectedCoin(e.target.value as "USDT" | "BTC" | "ETH")}
            className="bg-gray-200 dark:bg-secondary text-sm px-2 py-1 rounded border-none text-gray-600 dark:text-white"
          >
            <option value="USDT">USDT</option>
            <option value="BTC">BTC</option>
            <option value="ETH">ETH</option>
          </select>
        </div>
        <div className="text-xs text-muted-foreground mt-1">≈ ${usdValue.toFixed(2)}</div>
      </div>

      {/* Buttons */}
      <div className="flex sm:-mt-10 gap-2.5">
        <button className="w-full sm:w-auto bg-gray-200 dark:bg-secondary text-gray-600 dark:text-gray-400 border-none px-4 py-2 rounded cursor-pointer hover:scale-105 transition-transform">
          Deposit
        </button>
        <button className="w-full sm:w-auto bg-gray-200 dark:bg-secondary text-gray-600 dark:text-gray-400 border-none px-4 py-2 rounded cursor-pointer hover:scale-105 transition-transform">
          Withdraw
        </button>
      </div>
    </div>
  );
}
