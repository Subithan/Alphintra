'use client';

import React, { useState, useMemo } from 'react';
import { Search, Filter, TrendingUp, Star, Users, Trophy, MessageSquare, Book, Grid, List, ChevronDown, Eye, X, Twitter } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

// Theme hook replacement
const useTheme = () => {
  const [theme, setTheme] = React.useState('dark');
  
  React.useEffect(() => {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setTheme(isDark ? 'dark' : 'light');
  }, []);
  
  return { theme, setTheme };
};

interface Strategy {
  id: string;
  name: string;
  creatorId: string;
  creatorName: string;
  description: string;
  category: string;
  assetType: string;
  tradingPairs: string[];
  price: number | 'free';
  pricingModel: 'SUBSCRIPTION' | 'REVENUE_SHARE' | 'FREE' | 'ONE_TIME';
  revenueSharePercentage?: number;
  riskLevel: 'low' | 'medium' | 'high';
  verificationStatus: 'PENDING' | 'APPROVED' | 'REJECTED';
  performance: {
    totalReturn: number;
    annualizedReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    winRate: number;
  };
  rating: number;
  reviewCount: number;
  subscriberCount: number;
  lastUpdated: string;
  isVerified: boolean;
  thumbnail: string;
  gradientColors: string[];
}

const mockStrategies: Strategy[] = [
  {
    id: '1',
    name: 'Bitcoin devil',
    creatorId: 'creator1',
    creatorName: 'Amar',
    description: 'Bull rider',
    category: 'Momentum',
    assetType: 'Cryptocurrency',
    tradingPairs: ['BTC/USDT', 'ETH/USDT'],
    price: 99.99,
    pricingModel: 'SUBSCRIPTION',
    revenueSharePercentage: 30,
    riskLevel: 'medium',
    verificationStatus: 'APPROVED',
    performance: {
      totalReturn: 152.3,
      annualizedReturn: 85.6,
      maxDrawdown: -10.2,
      sharpeRatio: 2.4,
      winRate: 68.5,
    },
    rating: 5,
    reviewCount: 2,
    subscriberCount: 342,
    lastUpdated: '2025-08-15',
    isVerified: true,
    thumbnail: 'bull-rider',
    gradientColors: ['#1e3a8a', '#3b82f6', '#60a5fa'],
  },
  {
    id: '2',
    name: 'Bitcoin devil',
    creatorId: 'creator2',
    creatorName: 'Sophia',
    description: 'Bear trader',
    category: 'Arbitrage',
    assetType: 'Cryptocurrency',
    tradingPairs: ['BTC/USDT', 'LTC/USDT'],
    price: 149,
    pricingModel: 'ONE_TIME',
    revenueSharePercentage: 20,
    riskLevel: 'low',
    verificationStatus: 'PENDING',
    performance: {
      totalReturn: 78.9,
      annualizedReturn: 35.2,
      maxDrawdown: -3.4,
      sharpeRatio: 1.8,
      winRate: 74.1,
    },
    rating: 4.3,
    reviewCount: 95,
    subscriberCount: 158,
    lastUpdated: '2025-07-20',
    isVerified: false,
    thumbnail: 'bear-trader',
    gradientColors: ['#7c2d12', '#dc2626', '#ef4444'],
  },
  {
    id: '3',
    name: 'WOLF AI',
    creatorId: 'creator3',
    creatorName: 'Ravi',
    description: 'Computational Biology - WOLF AI',
    category: 'Quantitative',
    assetType: 'Equities',
    tradingPairs: ['AAPL/USD', 'TSLA/USD'],
    price: 199,
    pricingModel: 'SUBSCRIPTION',
    revenueSharePercentage: 40,
    riskLevel: 'high',
    verificationStatus: 'APPROVED',
    performance: {
      totalReturn: 245.6,
      annualizedReturn: 112.4,
      maxDrawdown: -18.7,
      sharpeRatio: 3.1,
      winRate: 61.3,
    },
    rating: 4.9,
    reviewCount: 276,
    subscriberCount: 487,
    lastUpdated: '2025-08-25',
    isVerified: true,
    thumbnail: 'market-reversal',
    gradientColors: ['#831843', '#db2777', '#ec4899'],
  },
  {
    id: '4',
    name: 'WOLF AI',
    creatorId: 'creator4',
    creatorName: 'Emma',
    description: 'AI Computational Biology - WOLF AI',
    category: 'AI Trading',
    assetType: 'Cryptocurrency',
    tradingPairs: ['ETH/USDT', 'SOL/USDT'],
    price: 299,
    pricingModel: 'SUBSCRIPTION',
    revenueSharePercentage: 35,
    riskLevel: 'high',
    verificationStatus: 'APPROVED',
    performance: {
      totalReturn: 312.4,
      annualizedReturn: 145.8,
      maxDrawdown: -15.3,
      sharpeRatio: 2.9,
      winRate: 65.7,
    },
    rating: 4.8,
    reviewCount: 234,
    subscriberCount: 521,
    lastUpdated: '2025-08-28',
    isVerified: true,
    thumbnail: 'ai-confirmation',
    gradientColors: ['#065f46', '#10b981', '#34d399'],
  },
  {
    id: '5',
    name: 'Dip Raider',
    creatorId: 'creator5',
    creatorName: 'Marcus',
    description: 'Pullback Warrior Strategy - Bynik',
    category: 'Mean Reversion',
    assetType: 'Cryptocurrency',
    tradingPairs: ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],
    price: 79,
    pricingModel: 'SUBSCRIPTION',
    revenueSharePercentage: 25,
    riskLevel: 'medium',
    verificationStatus: 'APPROVED',
    performance: {
      totalReturn: 189.7,
      annualizedReturn: 92.3,
      maxDrawdown: -12.8,
      sharpeRatio: 2.2,
      winRate: 70.4,
    },
    rating: 4.6,
    reviewCount: 167,
    subscriberCount: 398,
    lastUpdated: '2025-08-20',
    isVerified: true,
    thumbnail: 'dip-raider',
    gradientColors: ['#581c87', '#a855f7', '#c084fc'],
  },
  {
    id: '6',
    name: 'Apex AI Trend 5 min',
    creatorId: 'creator6',
    creatorName: 'Sarah',
    description: 'High-frequency trend following - Ryze',
    category: 'Trend Following',
    assetType: 'Cryptocurrency',
    tradingPairs: ['BTC/USDT', 'ETH/USDT'],
    price: 129,
    pricingModel: 'SUBSCRIPTION',
    revenueSharePercentage: 30,
    riskLevel: 'high',
    verificationStatus: 'APPROVED',
    performance: {
      totalReturn: 278.3,
      annualizedReturn: 128.5,
      maxDrawdown: -16.9,
      sharpeRatio: 2.7,
      winRate: 63.2,
    },
    rating: 4.7,
    reviewCount: 203,
    subscriberCount: 445,
    lastUpdated: '2025-08-29',
    isVerified: true,
    thumbnail: 'apex-5min',
    gradientColors: ['#1e40af', '#3b82f6', '#60a5fa'],
  },
  {
    id: '7',
    name: 'Apex AI Trend 4 hours',
    creatorId: 'creator7',
    creatorName: 'David',
    description: 'Medium-term trend strategy - Ryze',
    category: 'Trend Following',
    assetType: 'Cryptocurrency',
    tradingPairs: ['BTC/USDT', 'ETH/USDT'],
    price: 149,
    pricingModel: 'SUBSCRIPTION',
    revenueSharePercentage: 30,
    riskLevel: 'medium',
    verificationStatus: 'APPROVED',
    performance: {
      totalReturn: 195.8,
      annualizedReturn: 98.7,
      maxDrawdown: -11.3,
      sharpeRatio: 2.5,
      winRate: 69.8,
    },
    rating: 4.8,
    reviewCount: 221,
    subscriberCount: 512,
    lastUpdated: '2025-08-30',
    isVerified: true,
    thumbnail: 'apex-4h',
    gradientColors: ['#1e40af', '#3b82f6', '#60a5fa'],
  },
  {
    id: '8',
    name: 'Apex AI Trend 1 minute',
    creatorId: 'creator8',
    creatorName: 'Lisa',
    description: 'Ultra high-frequency scalping - Ryze',
    category: 'Scalping',
    assetType: 'Cryptocurrency',
    tradingPairs: ['BTC/USDT', 'ETH/USDT'],
    price: 179,
    pricingModel: 'SUBSCRIPTION',
    revenueSharePercentage: 35,
    riskLevel: 'high',
    verificationStatus: 'APPROVED',
    performance: {
      totalReturn: 298.4,
      annualizedReturn: 142.6,
      maxDrawdown: -19.2,
      sharpeRatio: 2.6,
      winRate: 61.9,
    },
    rating: 4.6,
    reviewCount: 189,
    subscriberCount: 456,
    lastUpdated: '2025-08-31',
    isVerified: true,
    thumbnail: 'apex-1min',
    gradientColors: ['#1e40af', '#3b82f6', '#60a5fa'],
  },
];

export default function MarketplacePage() {
  const { theme } = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('popularity');
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [filters, setFilters] = useState({
    assetType: 'all',
    riskLevel: 'all',
    priceRange: 'all',
    rating: 0,
    verificationStatus: 'all',
  });

  const filteredStrategies = useMemo(() => {
    return mockStrategies
      .filter((strategy) => {
        const matchesSearch =
          strategy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          strategy.creatorName.toLowerCase().includes(searchQuery.toLowerCase()) ||
          strategy.description.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesCategory = selectedCategory === 'all' || strategy.category.toLowerCase() === selectedCategory.toLowerCase();
        const matchesAssetType = filters.assetType === 'all' || strategy.assetType.toLowerCase() === filters.assetType.toLowerCase();
        const matchesRiskLevel = filters.riskLevel === 'all' || strategy.riskLevel === filters.riskLevel;
        const matchesRating = strategy.rating >= filters.rating;
        const matchesVerification = filters.verificationStatus === 'all' || strategy.verificationStatus === filters.verificationStatus;

        return matchesSearch && matchesCategory && matchesAssetType && matchesRiskLevel && matchesRating && matchesVerification;
      })
      .sort((a, b) => {
        switch (sortBy) {
          case 'roi-desc':
            return b.performance.totalReturn - a.performance.totalReturn;
          case 'rating':
            return b.rating - a.rating;
          case 'price-asc':
            const priceA = a.price === 'free' ? 0 : a.price;
            const priceB = b.price === 'free' ? 0 : b.price;
            return priceA - priceB;
          case 'popularity':
            return b.subscriberCount - a.subscriberCount;
          default:
            return 0;
        }
      });
  }, [searchQuery, selectedCategory, filters, sortBy]);

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className={`${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Marketplace</span>
              <span className={`text-sm ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`}>&gt;</span>
              <span className={`text-sm font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>Strategies</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex flex-wrap gap-3 mb-6">
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="All sorted" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All sorted</SelectItem>
              <SelectItem value="momentum">Momentum</SelectItem>
              <SelectItem value="mean-reversion">Mean Reversion</SelectItem>
              <SelectItem value="trend">Trend Following</SelectItem>
              <SelectItem value="arbitrage">Arbitrage</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filters.assetType} onValueChange={(value) => setFilters({ ...filters, assetType: value })}>
            <SelectTrigger className="w-52">
              <SelectValue placeholder="Free & paid Strategies" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Free & paid Strategies</SelectItem>
              <SelectItem value="free">Free Only</SelectItem>
              <SelectItem value="paid">Paid Only</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {filteredStrategies.map((strategy) => (
            <StrategyVisualCard 
              key={strategy.id} 
              strategy={strategy}
              onClick={() => setSelectedStrategy(strategy)}
            />
          ))}
        </div>
      </div>

      {selectedStrategy && (
        <StrategyModal 
          strategy={selectedStrategy} 
          onClose={() => setSelectedStrategy(null)}
        />
      )}
    </div>
  );
}

interface StrategyVisualCardProps {
  strategy: Strategy;
  onClick: () => void;
}

const StrategyVisualCard: React.FC<StrategyVisualCardProps> = ({ strategy, onClick }) => {
  const { theme } = useTheme();
  
  const getGradientStyle = (colors: string[]) => ({
    background: `linear-gradient(135deg, ${colors.join(', ')})`,
  });

  const getThumbnailContent = () => {
    switch (strategy.thumbnail) {
      case 'bull-rider':
        return (
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center">
              <div className="text-4xl mb-2">₿</div>
              <div className="text-xl font-bold text-white mb-1">{strategy.name}</div>
              <div className="text-3xl font-black text-white">{strategy.description}</div>
            </div>
          </div>
        );
      case 'bear-trader':
        return (
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center">
              <div className="text-4xl mb-2">₿</div>
              <div className="text-xl font-bold text-white mb-1">{strategy.name}</div>
              <div className="text-3xl font-black text-white">{strategy.description}</div>
            </div>
          </div>
        );
      case 'market-reversal':
        return (
          <div className="relative w-full h-full flex flex-col items-center justify-center p-4">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center w-full">
              <div className="text-4xl font-black text-white mb-2">MARKET REVERSAL</div>
              <div className="flex items-center justify-center gap-2 mb-2">
                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-sm">🐺</span>
                </div>
                <span className="text-lg font-bold text-white">WOLF AI</span>
              </div>
            </div>
          </div>
        );
      case 'ai-confirmation':
        return (
          <div className="relative w-full h-full flex flex-col items-center justify-center p-4">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center w-full">
              <div className="text-4xl font-black text-white mb-2">AI CONFIRMATION</div>
              <div className="flex items-center justify-center gap-2 mb-2">
                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-sm">🐺</span>
                </div>
                <span className="text-lg font-bold text-white">WOLF AI</span>
              </div>
            </div>
          </div>
        );
      case 'dip-raider':
        return (
          <div className="relative w-full h-full flex items-center justify-center p-4">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center">
              <div className="text-5xl font-black text-white leading-tight">
                DIP<br/>RAIDER
              </div>
            </div>
          </div>
        );
      default:
        const timeframe = strategy.thumbnail === 'apex-5min' ? '5 MINUTES' : 
                         strategy.thumbnail === 'apex-4h' ? '4 HOURS' : '1 MINUTE';
        return (
          <div className="relative w-full h-full flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-gradient-to-br from-gray-700 via-gray-800 to-gray-900"></div>
            <div className="relative z-10 text-center">
              <div className="text-4xl font-black text-white mb-2">APEX AI<br/>TREND</div>
              <div className="text-2xl font-bold text-white mb-4">{timeframe}</div>
              <div className="flex items-center justify-center gap-2">
                <span className="text-orange-500 font-bold">RYZE</span>
                <span className="text-white font-bold">×</span>
                <span className="text-red-500 font-bold">TRADE</span>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div 
      onClick={onClick}
      className={`rounded-lg overflow-hidden ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} border ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} hover:shadow-xl transition-all cursor-pointer hover:scale-105`}
    >
      <div className="relative h-48 w-full overflow-hidden">
        {getThumbnailContent()}
        {strategy.isVerified && (
          <div className="absolute top-2 right-2 w-8 h-8 bg-white/90 rounded-full flex items-center justify-center backdrop-blur-sm">
            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className={`font-semibold text-sm ${theme === 'dark' ? 'text-white' : 'text-gray-900'} line-clamp-1`}>
              {strategy.name}
            </h3>
            <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              {strategy.description}
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs mb-3">
          <div className="flex items-center gap-1">
            <Star className="h-3 w-3 text-yellow-500 fill-yellow-500" />
            <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>{strategy.rating}</span>
          </div>
          <div className="flex items-center gap-1">
            <Eye className="h-3 w-3 text-gray-400" />
            <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>{strategy.subscriberCount}</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className={`text-lg font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {strategy.price === 'free' ? 'Free' : `$${strategy.price}`}
          </span>
          {strategy.price !== 'free' && (
            <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              {strategy.pricingModel === 'SUBSCRIPTION' ? '/month' : 'one-time'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

interface StrategyModalProps {
  strategy: Strategy;
  onClose: () => void;
}

const StrategyModal: React.FC<StrategyModalProps> = ({ strategy, onClose }) => {
  const { theme } = useTheme();

  const getGradientStyle = (colors: string[]) => ({
    background: `linear-gradient(135deg, ${colors.join(', ')})`,
  });

  const getThumbnailContent = () => {
    switch (strategy.thumbnail) {
      case 'bull-rider':
      case 'bear-trader':
        return (
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center">
              <div className="text-6xl mb-4">₿</div>
              <div className="text-3xl font-bold text-white mb-2">{strategy.name}</div>
              <div className="text-5xl font-black text-white">{strategy.description}</div>
            </div>
          </div>
        );
      default:
        return (
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="absolute inset-0" style={getGradientStyle(strategy.gradientColors)}></div>
            <div className="relative z-10 text-center">
              <div className="text-4xl font-bold text-white">{strategy.name}</div>
              <div className="text-2xl font-medium text-white mt-2">{strategy.description}</div>
            </div>
          </div>
        );
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/60 backdrop-blur-md"></div>
      
      <div 
        className={`relative max-w-lg w-full ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} rounded-2xl shadow-2xl overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 w-8 h-8 flex items-center justify-center rounded-full bg-black/30 hover:bg-black/50 text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="relative h-64 w-full">
          {getThumbnailContent()}
        </div>

        <div className="p-6">
          <h2 className={`text-2xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
            {strategy.name} - {strategy.description}
          </h2>

          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-1">
              <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Type:</span>
              <Badge className="bg-cyan-500 text-white">Strategy</Badge>
            </div>
            <div className="flex items-center gap-1">
              {[...Array(5)].map((_, i) => (
                <Star 
                  key={i} 
                  className={`h-4 w-4 ${i < Math.floor(strategy.rating) ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'}`}
                />
              ))}
              <span className={`text-sm ml-1 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                ({strategy.reviewCount})
              </span>
            </div>
          </div>

          <Button className="w-full bg-cyan-500 hover:bg-cyan-600 text-white mb-4">
            Buy ${typeof strategy.price === 'number' ? strategy.price.toFixed(2) : '0.00'}
          </Button>

          <p className={`text-xs text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} mb-4`}>
            Price includes 1 month of updates.
          </p>

          <div className="flex justify-center">
            <button className="flex items-center gap-2 text-gray-400 hover:text-gray-600 transition-colors">
              <Twitter className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};