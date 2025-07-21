'use client';

import BalanceCard from "@/components/ui/dashboard/BalanceCard";
import CryptoTable from "@/components/ui/dashboard/cryptoTable";
import NewsCard from "@/components/ui/dashboard/newsCard";
import PriceChart from "@/components/ui/dashboard/PriceChart";
import { MoreHorizontal } from 'lucide-react';
import GradientBorder from '@/components/ui/GradientBorder';

export default function Dashboard() {
  return (
    <>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 overflow-x-hidden">
  <div className="col-span-5 lg:col-start-1 lg:col-end-4 flex flex-col gap-8">
    <GradientBorder gradientAngle="275deg" className="p-5">
      <BalanceCard />
    </GradientBorder>
    <GradientBorder gradientAngle="275deg" className="p-5">
      <CryptoTable />
    </GradientBorder>
  </div>
  <div className="col-span-5 lg:col-start-4 lg:col-end-6 flex flex-col gap-8">
    <GradientBorder gradientAngle="315deg" className="p-5">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-white text-xl font-bold">BREAKING NEWS</h2>
        <div className="text-gray-400 hover:text-white cursor-pointer">
          <MoreHorizontal className="w-6 h-6" />
        </div>
      </div>
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
    </GradientBorder>
    <GradientBorder gradientAngle="315deg" className="p-5">
      <PriceChart price={31928} />
    </GradientBorder>
  </div>
</div>
    </>
  );
}