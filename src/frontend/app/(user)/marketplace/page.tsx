'use client';

import React, { useState, useMemo } from 'react';
import { Search, Filter, TrendingUp, Star, Users, Trophy, MessageSquare, Book, Download, Grid, List, ChevronDown } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { useTheme } from 'next-themes';
import StrategyCard from '@/components/marketplace/StrategyCard';
import FilterSidebar from '@/components/marketplace/FilterSidebar';
import CommunityForum from '@/components/marketplace/CommunityForum';
import Leaderboard from '@/components/marketplace/Leaderboard';
import SocialTradingPanel from '@/components/marketplace/SocialTradingPanel';
import EducationalContent from '@/components/marketplace/EducationalContent';

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
  pricingModel: 'SUBSCRIPTION' | 'REVENUE_SHARE' | 'FREE';
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
}

interface LeaderboardEntry {
  id: string;
  userId: string;
  username: string;
  rank: number;
  totalReturn: number;
  sharpeRatio: number;
  winRate: number;
}

interface ForumTopic {
  id: string;
  title: string;
  category: string;
  author: string;
  replyCount: number;
  viewCount: number;
  lastReplyAt: string;
}

const mockStrategies: Strategy[] = [
  {
    id: '1',
    name: 'Alpha Momentum Strategy',
    creatorId: 'creator1',
    creatorName: 'TradeMaster',
    description: 'High-performance momentum strategy for crypto markets',
    category: 'Momentum',
    assetType: 'Cryptocurrency',
    tradingPairs: ['BTC/USDT', 'ETH/USDT'],
    price: 99,
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
    rating: 4.7,
    reviewCount: 189,
    subscriberCount: 342,
    lastUpdated: '2025-08-15',
    isVerified: true,
  },
  // Additional mock strategies...
];

const mockLeaderboard: LeaderboardEntry[] = [
  {
    id: '1',
    userId: 'user1',
    username: 'CryptoKing',
    rank: 1,
    totalReturn: 245.7,
    sharpeRatio: 2.8,
    winRate: 72.3,
  },
  // Additional mock leaderboard entries...
];

const mockForumTopics: ForumTopic[] = [
  {
    id: '1',
    title: 'Best Practices for Momentum Trading',
    category: 'Trading Strategies',
    author: 'TradeMaster',
    replyCount: 45,
    viewCount: 1234,
    lastReplyAt: '2025-08-30',
  },
  // Additional mock forum topics...
];

export default function MarketplacePage() {
  const { theme } = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('popularity');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [activeTab, setActiveTab] = useState('strategies');
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
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-slate-900' : 'bg-gray-100'}`}>
      {/* Header */}
      <div className={`${theme === 'dark' ? 'bg-slate-800' : 'bg-white'} border-b ${theme === 'dark' ? 'border-slate-700' : 'border-gray-200'} sticky top-0 z-10 shadow-lg`}>
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <h1 className={`text-3xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                Alphintra Marketplace
              </h1>
              <p className={`text-lg ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'} mt-1`}>
                Discover, share, and monetize trading strategies with our vibrant community
              </p>
            </div>
            <div className="flex gap-3">
              <Button className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white">
                Become a Creator
              </Button>
              <Button variant="outline" className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Join Community
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Search and Controls */}
        <div className="flex flex-col lg:flex-row gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <Input
              placeholder="Search strategies, creators, or topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-12"
            />
          </div>
          <div className="flex flex-wrap gap-3">
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="momentum">Momentum</SelectItem>
                <SelectItem value="mean-reversion">Mean Reversion</SelectItem>
                <SelectItem value="grid-trading">Grid Trading</SelectItem>
                <SelectItem value="arbitrage">Arbitrage</SelectItem>
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="popularity">Most Popular</SelectItem>
                <SelectItem value="roi-desc">Highest ROI</SelectItem>
                <SelectItem value="rating">Top Rated</SelectItem>
                <SelectItem value="price-asc">Price: Low to High</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2"
            >
              <Filter className="h-4 w-4" />
              Filters
            </Button>
            <div className="flex border rounded-lg overflow-hidden">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('grid')}
                className="rounded-none"
              >
                <Grid className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('list')}
                className="rounded-none"
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="flex flex-wrap gap-6 mb-6">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'}`}>
              {filteredStrategies.length} strategies found
            </span>
          </div>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-500" />
            <span className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'}`}>
              Avg ROI: {filteredStrategies.reduce((sum, s) => sum + s.performance.totalReturn, 0) / (filteredStrategies.length || 1)}%
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Star className="h-4 w-4 text-yellow-500" />
            <span className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'}`}>
              Avg Rating: {(filteredStrategies.reduce((sum, s) => sum + s.rating, 0) / (filteredStrategies.length || 1)).toFixed(1)}/5
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-purple-500" />
            <span className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'}`}>
              {filteredStrategies.reduce((sum, s) => sum + s.subscriberCount, 0)} active subscribers
            </span>
          </div>
        </div>

        <div className="flex gap-6">
          {/* Filter Sidebar */}
          {showFilters && (
            <div className="w-64 flex-shrink-0">
              <FilterSidebar
                filters={filters}
                onFiltersChange={setFilters}
                additionalFilters={[
                  {
                    label: 'Verification Status',
                    key: 'verificationStatus',
                    options: ['all', 'APPROVED', 'PENDING'],
                  },
                ]}
              />
            </div>
          )}

          {/* Main Content */}
          <div className="flex-1">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-5 mb-6">
                <TabsTrigger value="strategies">Strategies</TabsTrigger>
                <TabsTrigger value="community">Community</TabsTrigger>
                <TabsTrigger value="social">Social Trading</TabsTrigger>
                <TabsTrigger value="leaderboards">Leaderboards</TabsTrigger>
                <TabsTrigger value="education">Education</TabsTrigger>
              </TabsList>

              {/* Strategies Tab */}
              <TabsContent value="strategies" className="space-y-0">
                {filteredStrategies.length === 0 ? (
                  <div className={`text-center py-12 ${theme === 'dark' ? 'text-slate-400' : 'text-gray-600'}`}>
                    <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">No strategies found matching your criteria</p>
                    <p className="text-sm mt-2">Try adjusting your search or filters</p>
                  </div>
                ) : (
                  <div
                    className={
                      viewMode === 'grid'
                        ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6'
                        : 'space-y-4'
                    }
                  >
                    {filteredStrategies.map((strategy) => (
                      <StrategyCard
                        key={strategy.id}
                        strategy={strategy}
                        viewMode={viewMode}
                        onSubscribe={() => console.log(`Subscribe to ${strategy.id}`)}
                        onReview={() => console.log(`Review ${strategy.id}`)}
                      />
                    ))}
                  </div>
                )}
             
             