'use client';

import BalanceCard from "@/components/ui/dashboard/BalanceCard";
import CryptoTable from "@/components/ui/dashboard/cryptoTable";
import NewsCard from "@/components/ui/dashboard/newsCard";
import PriceChart from "@/components/ui/dashboard/PriceChart";
import { MoreHorizontal } from 'lucide-react';

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Balance Card */}
        <div className="lg:col-span-2">
          <div className="p-6 rounded-xl bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 shadow-lg dark:shadow-xl border transition-all hover:shadow-2xl">
            <BalanceCard />
          </div>
        </div>

        {/* News Section */}
        <div className="p-6 rounded-xl bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 shadow-lg dark:shadow-xl border">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-red-500/10">
                <MoreHorizontal className="w-5 h-5 text-red-500" />
              </div>
              <h2 className="text-gray-900 dark:text-white text-xl font-bold">BREAKING NEWS</h2>
            </div>
          </div>
          <div className="space-y-3">
            <NewsCard 
              title="Metaverse already needs competition scrutiny, says EU antitrust chief:"
              source="Cointelegraph"
              time="30 min ago"
            />
            <NewsCard 
              title="New AI Regulations Proposed in EU Parliament:"
              source="TechCrunch"
              time="1 hour ago"
            />
            <NewsCard 
              title="SpaceX Successfully Launches Latest Satellite:"
              source="SpaceNews"
              time="2 hours ago"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Crypto Table */}
        <div className="lg:col-span-2">
          <div className="p-6 rounded-xl bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 shadow-lg dark:shadow-xl border">
            <CryptoTable />
          </div>
        </div>

        {/* Price Chart */}
        <div className="p-6 rounded-xl bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 shadow-lg dark:shadow-xl border">
          <PriceChart price={31928} />
        </div>
      </div>
    </div>
  );
}