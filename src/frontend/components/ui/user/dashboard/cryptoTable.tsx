"use client";

import React, { useState } from "react";
import useSWR from "swr";
import { cn } from "@/lib/utils";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { coinfetcher } from "@/lib/api/fetcher";
import { Coin } from "@/lib/api/types";
import { useTheme } from "next-themes";

const rowsPerPage = 10;

export default function CryptoTable() {
  const [currentPage, setCurrentPage] = useState(1);
  const { resolvedTheme } = useTheme();

  // Fetch data from CoinGecko API
  const { data, error, isLoading } = useSWR<Coin[]>(
    `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false&price_change_percentage=24h`,
    coinfetcher,
    { refreshInterval: 60000 } // Refresh every minute
  );

  // Handle loading and error states
  if (error)
    return <div className="text-center text-red-500">Failed to load data</div>;
  if (isLoading) return <div className="text-center text-white">Loading...</div>;

  // Calculate total pages based on fetched data
  const totalPages = Math.ceil((data?.length || 0) / rowsPerPage);

  // Paginate the data
  const paginatedData = data?.slice(
    (currentPage - 1) * rowsPerPage,
    currentPage * rowsPerPage
  ) || [];

  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages) setCurrentPage(page);
  };

  const getSmartPages = (current: number, total: number): (number | string)[] => {
    const delta = 1;
    const pages: (number | string)[] = [];

    for (let i = 1; i <= total; i++) {
      if (
        i === 1 ||
        i === total ||
        (i >= current - delta && i <= current + delta)
      ) {
        pages.push(i);
      } else if (pages[pages.length - 1] !== "...") {
        pages.push("...");
      }
    }

    return pages;
  };

  return (
    <div className={cn(
      "p-4",
      resolvedTheme === "dark" ? "text-white" : "text-black"
    )}>
      {/* Table */}
      <div
        className={cn(
          "overflow-x-auto rounded-lg",
          resolvedTheme === "dark" ? "bg-[#0a0a1a]" : "bg-white"
        )}
      >
        <table className="min-w-full text-sm text-left">
          <thead
            className={cn(
              "uppercase text-xs",
              resolvedTheme === "dark"
                ? "bg-[#101020] text-gray-400"
                : "bg-gray-200 text-gray-600"
            )}
          >
            <tr>
              <th className="px-4 py-3">Coin</th>
              <th className="px-4 py-3">Symbol</th>
              <th className="px-4 py-3">Price (USD)</th>
              <th className="px-4 py-3">Market Cap</th>
              <th className="px-4 py-3">24h Change</th>
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((coin, i) => (
              <tr
                key={coin.id}
                className={cn(
                  "border-b hover:bg-opacity-30",
                  resolvedTheme === "dark"
                    ? "border-[#1a1a2e] hover:bg-[#141426]"
                    : "border-gray-300 hover:bg-gray-100"
                )}
              >
                <td className="px-4 py-3 font-bold flex items-center gap-2">
                  <span>{String((currentPage - 1) * rowsPerPage + i + 1).padStart(2, "0")}</span>
                  <img src={coin.image} alt={coin.name} className="w-6 h-6" />
                  <span>{coin.name}</span>
                </td>
                <td className={resolvedTheme === "dark" ? "text-white" : "text-black"}>
                  {coin.symbol.toUpperCase()}
                </td>
                <td className={resolvedTheme === "dark" ? "text-white" : "text-black"}>
                  ${coin.current_price.toLocaleString("en-US", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </td>
                <td className={resolvedTheme === "dark" ? "text-white" : "text-black"}>
                  ${coin.market_cap.toLocaleString("en-US")}
                </td>
                <td
                  className={cn(
                    "px-4 py-3",
                    coin.price_change_percentage_24h >= 0
                      ? "text-green-500"
                      : "text-red-500"
                  )}
                >
                  {coin.price_change_percentage_24h.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-center mt-4 text-gray-400 gap-1 items-center">
        <button
          className="w-8 h-8 hover:text-yellow-500"
          disabled={currentPage === 1}
          onClick={() => goToPage(currentPage - 1)}
        >
          <ChevronLeft size={16} />
        </button>
        {getSmartPages(currentPage, totalPages).map((num, idx) =>
          typeof num === "number" ? (
            <button
              key={idx}
              onClick={() => goToPage(num)}
              className={cn(
                "w-6 h-6 rounded-lg text-sm",
                num === currentPage
                  ? "border border-yellow-500 text-yellow-500"
                  :  resolvedTheme === "dark"
                  ? "hover:text-white"
                  : "hover:text-black"
              )}
            >
              {num}
            </button>
          ) : (
            <span key={idx} className="px-2">
              ...
            </span>
          )
        )}
        <button
          className="w-8 h-8 hover:text-yellow-500"
          disabled={currentPage === totalPages}
          onClick={() => goToPage(currentPage + 1)}
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}