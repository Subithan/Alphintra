"use client";

import React from "react";
// import BitcoinChart from "./BitCoinChart"; // Temporarily disabled - file missing

export default function PriceChart() {
  return (
    <div className="p-0 text-foreground">
      <div className="flex justify-between items-center mb-2 px-2 pt-2 pb-0">
        <div className="text-xl font-bold">BITCOIN</div>
      </div>
      <div className="-pl-4 m-0 pt-0 pb-0">
        <div className="p-4 text-center text-muted-foreground">
          {/* BitcoinChart component temporarily disabled - file missing */}
          <p>Chart component loading...</p>
        </div>
      </div>
    </div>
  );
}
