'use client';

import React, { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';

export default function BalanceCard() {
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);
  if (!mounted) return null;
  const currentTheme = theme === 'system' ? systemTheme : theme;

  return (
      <div className={`p-4 rounded-lg ${currentTheme === 'dark' ? 'bg-[#0a0a1a] border border-yellow-500/20 hover:bg-[#141426] text-white' : 'bg-gray-50 border border-gray-200 hover:bg-gray-100 text-gray-900'} flex justify-between items-center transition-all`}>
        <div>
          <div className="text-xl font-bold">Estimated Balance</div>
          <div className="text-2xl font-bold">
            0.00 USDT <span className={`${currentTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>▼</span>
          </div>
          <div className="text-xs">≈ $0.00</div>
        </div>
        <div className="flex -mt-10 gap-2.5">
          <button className={`${currentTheme === 'dark' ? 'bg-gray-700 text-white hover:bg-gray-600' : 'bg-gray-200 text-gray-900 hover:bg-gray-300'} border-none px-4 py-1 rounded cursor-pointer transition-colors`}>
            Deposit
          </button>
          <button className={`${currentTheme === 'dark' ? 'bg-gray-700 text-white hover:bg-gray-600' : 'bg-gray-200 text-gray-900 hover:bg-gray-300'} border-none px-4 py-1 rounded cursor-pointer transition-colors`}>
            Withdraw
          </button>
        </div>
      </div>
  );
}