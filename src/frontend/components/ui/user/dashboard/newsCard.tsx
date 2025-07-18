"use client";

import React from "react";
import useSWR from "swr";
import { Megaphone } from "lucide-react";
import { newsFetcher } from "@/lib/api/fetcher";
import { NewsItem } from "@/lib/api/types";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils"; // your classnames helper

const NewsCard: React.FC = () => {
  const { resolvedTheme } = useTheme();

  const { data, error, isLoading } = useSWR<{ Data: NewsItem[] }>(
    `https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories=Cryptocurrency&api_key=${process.env.NEXT_PUBLIC_CRYPTOCOMPARE_API_KEY || ''}`,
    newsFetcher,
    { refreshInterval: 600000 } // Refresh every 10 minutes
  );

  if (error)
    return <div className="text-center text-yellow-500">Failed to load news</div>;
  if (isLoading)
    return (
      <div className={resolvedTheme === 'dark' ? 'text-white text-center' : 'text-black text-center'}>
        Loading news...
      </div>
    );

  const newsItems = data?.Data?.slice(0, 3) || [];

  return (
    <div className="space-y-4">
      {newsItems.map((news) => (
        <div
          key={news.id}
          className={cn(
            "border p-4 rounded-lg shadow-lg",
            resolvedTheme === "dark"
              ? "bg-[#0a0a1a] border-[#262739]"
              : "bg-white border-gray-300"
          )}
        >
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <Megaphone
                className={cn(
                  "w-5 h-5",
                  resolvedTheme === "dark" ? "text-yellow-500" : "text-yellow-600"
                )}
              />
            </div>
            <div className={cn(
              "text-sm font-bold leading-tight",
              resolvedTheme === "dark" ? "text-white" : "text-gray-900"
            )}>
              {news.title}
              <p className={cn(
                "text-xs mt-1",
                resolvedTheme === "dark" ? "text-gray-400" : "text-gray-600"
              )}>
                {news.source} ·{" "}
                {new Date(news.published_on * 1000).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "numeric",
                  minute: "numeric",
                })}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default NewsCard;
