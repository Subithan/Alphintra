import React from 'react';

export default function BalanceCard() {
  return (
      <div className="text-white flex justify-between items-center">
        <div>
          <div className="text-xl font-bold">Estimated Balance</div>
          <div className="text-2xl font-bold">
            0.00 USDT <span className="text-gray-400">▼</span>
          </div>
          <div className="text-xs">≈ $0.00</div>
        </div>
        <div className="flex -mt-10 gap-2.5">
          <button className="bg-gray-700 text-white border-none px-4 py-1 rounded cursor-pointer">
            Deposit
          </button>
          <button className="bg-gray-700 text-white border-none px-4 py-1 rounded cursor-pointer">
            Withdraw
          </button>
        </div>
      </div>
  );
}