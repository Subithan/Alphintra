'use client';

import * as React from 'react';
import Bot_detail from '@/components/ui/user/trade/Bot';
import TradingChart from '@/components/ui/user/trade/tradingViewWidget-light.tsx';
import OrderBook from '@/components/ui/user/trade/order-book';
import MainPanel from '@/components/ui/user/trade/main-panel';
import { Bot, Bell } from 'lucide-react';

export default function Trade() {
  return (
    <main className="flex-1 p-4 md:p-6 lg:p-8">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Top Row: Portfolio Summary */}
        <div className="col-span-1 lg:col-span-12">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Bot_detail/>
          </div>
        </div>

        {/* Middle Row: Chart and Order Book */}
        <div className="col-span-1 lg:col-span-9">
          <TradingChart />
        </div>
        <div className="col-span-1 lg:col-span-3">
          <OrderBook  />
        </div>

        {/* Bottom Row: Main Panel with Tabs */}
        <div className="col-span-1 lg:col-span-12">
          <MainPanel />
        </div>
      </div>
    </main>
  );
}