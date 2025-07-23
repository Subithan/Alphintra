'use client';

import React from 'react';
import { Star, TrendingUp, TrendingDown, Download, Shield, Crown, Eye, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { useTheme } from 'next-themes';
import Link from 'next/link';

interface Strategy {
  id: string;
  name: string;
  developer: string;
  description: string;
  roi: number;
  roiChange: number;
  tradingPairs: string[];
  rating: number;
  reviews: number;
  downloads: number;
  price: number | 'free';
  riskLevel: 'low' | 'medium' | 'high';
  category: string;
  assetType: string;
  version: string;
  lastUpdated: string;
  backtestResults: {
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
  };
  isPro: boolean;
  isVerified: boolean;
}

interface StrategyCardProps {
  strategy: Strategy;
  viewMode: 'grid' | 'list';
}

const getRiskColor = (level: string) => {
  switch (level) {
    case 'low': return 'text-green-500 bg-green-100 dark:bg-green-900/30';
    case 'medium': return 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/30';
    case 'high': return 'text-red-500 bg-red-100 dark:bg-red-900/30';
    default: return 'text-gray-500 bg-gray-100 dark:bg-gray-900/30';
  }
};

const formatPrice = (price: number | 'free') => {
  if (price === 'free') return 'Free';
  return `$${price}/month`;
};

const StrategyCard: React.FC<StrategyCardProps> = ({ strategy, viewMode }) => {
  const { theme } = useTheme();

  if (viewMode === 'list') {
    return (
      <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} hover:shadow-lg transition-all duration-200 group`}>
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row lg:items-center gap-6">
            {/* Main Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start gap-3 mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className={`font-semibold text-lg truncate ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {strategy.name}
                    </h3>
                    {strategy.isVerified && (
                      <Shield className="h-4 w-4 text-blue-500 flex-shrink-0" />
                    )}
                    {strategy.isPro && (
                      <Crown className="h-4 w-4 text-yellow-500 flex-shrink-0" />
                    )}
                  </div>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} mb-2`}>
                    by {strategy.developer}
                  </p>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'} line-clamp-2`}>
                    {strategy.description}
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mb-3">
                <Badge variant="outline" className={getRiskColor(strategy.riskLevel)}>
                  {strategy.riskLevel.toUpperCase()} RISK
                </Badge>
                <Badge variant="outline">{strategy.category}</Badge>
                <Badge variant="outline">{strategy.assetType}</Badge>
                {strategy.tradingPairs.slice(0, 2).map((pair) => (
                  <Badge key={pair} variant="secondary" className="text-xs">
                    {pair}
                  </Badge>
                ))}
                {strategy.tradingPairs.length > 2 && (
                  <Badge variant="secondary" className="text-xs">
                    +{strategy.tradingPairs.length - 2} more
                  </Badge>
                )}
              </div>
            </div>

            {/* Performance Stats */}
            <div className="flex flex-col lg:flex-row lg:items-center gap-6">
              <div className="flex flex-col items-center lg:items-start">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-2xl font-bold ${strategy.roi > 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {strategy.roi > 0 ? '+' : ''}{strategy.roi.toFixed(1)}%
                  </span>
                  <div className="flex items-center gap-1">
                    {strategy.roiChange > 0 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                    <span className={`text-sm font-medium ${strategy.roiChange > 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {strategy.roiChange > 0 ? '+' : ''}{strategy.roiChange.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                  Total ROI
                </span>
              </div>

              <div className="flex flex-col items-center lg:items-start">
                <div className="flex items-center gap-1 mb-1">
                  <Star className="h-4 w-4 text-yellow-500 fill-current" />
                  <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                    {strategy.rating.toFixed(1)}
                  </span>
                </div>
                <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                  {strategy.reviews} reviews
                </span>
              </div>

              <div className="flex flex-col items-center lg:items-start">
                <div className="flex items-center gap-1 mb-1">
                  <Download className="h-4 w-4 text-blue-500" />
                  <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                    {strategy.downloads.toLocaleString()}
                  </span>
                </div>
                <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                  downloads
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-2 lg:min-w-0 lg:w-auto">
              <div className="text-center mb-2">
                <span className={`text-lg font-bold ${strategy.price === 'free' ? 'text-green-500' : theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  {formatPrice(strategy.price)}
                </span>
              </div>
              <div className="flex gap-2">
                <Link href={`/marketplace/${strategy.id}`}>
                  <Button variant="outline" size="sm" className="flex items-center gap-1">
                    <Eye className="h-4 w-4" />
                    View Details
                  </Button>
                </Link>
                <Button 
                  className="bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-semibold flex items-center gap-1"
                  size="sm"
                >
                  Plug In
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Grid view
  return (
    <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} hover:shadow-lg hover:scale-[1.02] transition-all duration-200 group overflow-hidden`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <h3 className={`font-semibold text-lg truncate ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              {strategy.name}
            </h3>
            <div className="flex gap-1 flex-shrink-0">
              {strategy.isVerified && (
                <Shield className="h-4 w-4 text-blue-500" />
              )}
              {strategy.isPro && (
                <Crown className="h-4 w-4 text-yellow-500" />
              )}
            </div>
          </div>
          <Badge variant="outline" className={getRiskColor(strategy.riskLevel)}>
            {strategy.riskLevel.toUpperCase()}
          </Badge>
        </div>
        <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          by {strategy.developer}
        </p>
      </CardHeader>

      <CardContent className="py-0">
        <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'} line-clamp-3 mb-4`}>
          {strategy.description}
        </p>

        {/* ROI Display with Mini Chart Effect */}
        <div className="relative mb-4 p-4 rounded-lg bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-600">
          <div className="flex items-center justify-between mb-2">
            <span className={`text-xs font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
              TOTAL ROI
            </span>
            <div className="flex items-center gap-1">
              {strategy.roiChange > 0 ? (
                <TrendingUp className="h-3 w-3 text-green-500" />
              ) : (
                <TrendingDown className="h-3 w-3 text-red-500" />
              )}
              <span className={`text-xs font-medium ${strategy.roiChange > 0 ? 'text-green-500' : 'text-red-500'}`}>
                {strategy.roiChange > 0 ? '+' : ''}{strategy.roiChange.toFixed(1)}%
              </span>
            </div>
          </div>
          <div className={`text-2xl font-bold ${strategy.roi > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
            {strategy.roi > 0 ? '+' : ''}{strategy.roi.toFixed(1)}%
          </div>
          <div className="absolute bottom-0 right-0 w-16 h-8 opacity-20">
            <svg viewBox="0 0 64 32" className="w-full h-full">
              <polyline 
                points="0,24 16,16 32,20 48,8 64,12" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2"
                className={strategy.roi > 0 ? 'text-green-500' : 'text-red-500'}
              />
            </svg>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Star className="h-3 w-3 text-yellow-500 fill-current" />
              <span className={`text-sm font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                {strategy.rating.toFixed(1)}
              </span>
            </div>
            <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              {strategy.reviews} reviews
            </span>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Download className="h-3 w-3 text-blue-500" />
              <span className={`text-sm font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                {strategy.downloads > 999 ? `${(strategy.downloads / 1000).toFixed(1)}k` : strategy.downloads}
              </span>
            </div>
            <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              downloads
            </span>
          </div>
          <div className="text-center">
            <div className={`text-sm font-semibold mb-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              {strategy.backtestResults.winRate.toFixed(0)}%
            </div>
            <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              win rate
            </span>
          </div>
        </div>

        {/* Trading Pairs */}
        <div className="flex flex-wrap gap-1 mb-4">
          {strategy.tradingPairs.slice(0, 3).map((pair) => (
            <Badge key={pair} variant="secondary" className="text-xs">
              {pair}
            </Badge>
          ))}
          {strategy.tradingPairs.length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{strategy.tradingPairs.length - 3}
            </Badge>
          )}
        </div>

        {/* Category and Asset Type */}
        <div className="flex flex-wrap gap-2 mb-4">
          <Badge variant="outline">{strategy.category}</Badge>
          <Badge variant="outline">{strategy.assetType}</Badge>
        </div>
      </CardContent>

      <CardFooter className="flex flex-col gap-3 pt-0">
        <div className="flex items-center justify-between w-full">
          <span className={`text-lg font-bold ${strategy.price === 'free' ? 'text-green-500' : theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {formatPrice(strategy.price)}
          </span>
          <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
            v{strategy.version}
          </span>
        </div>
        
        <div className="flex gap-2 w-full">
          <Link href={`/marketplace/${strategy.id}`} className="flex-1">
            <Button variant="outline" className="w-full" size="sm">
              <Eye className="h-4 w-4 mr-1" />
              Details
            </Button>
          </Link>
          <Button 
            className="flex-1 bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-semibold"
            size="sm"
          >
            Plug In
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};

export default StrategyCard;