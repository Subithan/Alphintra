
'use client';

import * as React from 'react';
import Bot_detail from '@/components/ui/user/trade/Bot';
import TradingChart from '@/components/ui/user/trade/tradingViewWidget-light.tsx';
import OrderBook from '@/components/ui/user/trade/order-book';
import MainPanel from '@/components/ui/user/trade/main-panel';

export default function Trade() {
  const [refreshKey, setRefreshKey] = React.useState(0);
  const handleOrderPlaced = () => {
    setRefreshKey((prev) => prev + 1); 
  };

  return (
    <main className="flex-1 p-2 sm:p-4 md:p-6 lg:p-8">
      <div className="grid grid-cols-1 gap-4 sm:gap-6">
        {/* Top Row: Bot Control */}
        <div className="col-span-1">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 w-full">
              <Bot_detail />
            </div>
          </div>
        </div>

        {/* Middle Row: Chart and Order Book */}
        <div className="col-span-1 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="col-span-1 sm:col-span-2">
            <TradingChart />
          </div>
          <div className="col-span-1">
            <OrderBook />
          </div>
        </div>

        {/* Bottom Row: Main Panel with Tabs */}
        <div className="col-span-1">
          <MainPanel key={refreshKey} />
        </div>
      </div>
    </main>
  );
}
