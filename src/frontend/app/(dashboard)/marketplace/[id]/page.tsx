'use client';

import React, { useState } from 'react';
import { 
  ArrowLeft, Star, Download, Shield, Crown, TrendingUp, TrendingDown, 
  Calendar, Users, BarChart3, Activity, AlertTriangle, CheckCircle, 
  ExternalLink, Heart, Share2, Flag, MessageSquare, ChevronRight,
  Play, Pause, Settings
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { useTheme } from 'next-themes';
import Link from 'next/link';
import PerformanceChart from '@/components/marketplace/PerformanceChart';
import BacktestResults from '@/components/marketplace/BacktestResults';
import ReviewSection from '@/components/marketplace/ReviewSection';

// Mock data for detailed strategy view
const strategyDetail = {
  id: '1',
  name: 'Quantum Momentum Pro',
  developer: 'AlgoMaster',
  description: 'Advanced momentum strategy using quantum-inspired algorithms for crypto markets. This strategy leverages machine learning to identify optimal entry and exit points while managing risk through dynamic position sizing.',
  longDescription: `Quantum Momentum Pro represents the cutting edge of algorithmic trading, combining quantum-inspired optimization techniques with traditional momentum indicators. The strategy uses a multi-layered approach:

1. **Quantum Signal Processing**: Utilizes superposition principles to analyze multiple market states simultaneously
2. **Adaptive Risk Management**: Dynamic position sizing based on market volatility and correlation patterns
3. **Multi-Timeframe Analysis**: Incorporates signals from multiple timeframes for robust decision making
4. **Smart Exit Logic**: Advanced profit-taking and stop-loss mechanisms that adapt to market conditions

The algorithm has been extensively backtested across various market conditions and consistently outperforms traditional momentum strategies.`,
  roi: 142.5,
  roiChange: 12.3,
  tradingPairs: ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'],
  rating: 4.8,
  reviews: 247,
  downloads: 1523,
  price: 99,
  riskLevel: 'medium',
  category: 'Momentum',
  assetType: 'Cryptocurrency',
  version: '2.1.0',
  lastUpdated: '2024-01-15',
  backtestResults: {
    totalReturn: 142.5,
    sharpeRatio: 2.3,
    maxDrawdown: -8.5,
    winRate: 67.2,
    avgTrade: 2.8,
    profitFactor: 2.1,
    totalTrades: 1247,
    avgHoldingTime: '4.2 days'
  },
  isPro: true,
  isVerified: true,
  publishedDate: '2023-08-15',
  lastRevision: '2024-01-15',
  supportedExchanges: ['Binance', 'Coinbase Pro', 'Kraken', 'FTX', 'Bitfinex'],
  minCapital: 1000,
  maxPositions: 5,
  features: [
    'Real-time Signal Generation',
    'Risk Management Suite',
    'Backtesting Framework',
    'Performance Analytics',
    'Alert System',
    '24/7 Monitoring'
  ],
  requirements: {
    capital: '$1,000 minimum',
    exchanges: 'Supported exchanges required',
    api: 'API keys for live trading',
    experience: 'Intermediate to Advanced'
  }
};

export default function StrategyDetailPage({ params }: { params: { id: string } }) {
  const { theme } = useTheme();
  const [isLiked, setIsLiked] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-500 bg-green-100 dark:bg-green-900/30';
      case 'medium': return 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/30';
      case 'high': return 'text-red-500 bg-red-100 dark:bg-red-900/30';
      default: return 'text-gray-500 bg-gray-100 dark:bg-gray-900/30';
    }
  };

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <div className={`${theme === 'dark' ? 'bg-gray-800' : 'bg-white'} border-b ${theme === 'dark' ? 'border-gray-700' : 'border-gray-200'} sticky top-0 z-10`}>
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Link href="/marketplace">
              <Button variant="ghost" size="sm" className="flex items-center gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Marketplace
              </Button>
            </Link>
            <div className="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
            <nav className="flex items-center space-x-2 text-sm">
              <Link href="/marketplace" className={`${theme === 'dark' ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'}`}>
                Marketplace
              </Link>
              <span className={`${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>/</span>
              <span className={`${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                {strategyDetail.name}
              </span>
            </nav>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Strategy Header */}
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <CardHeader>
                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h1 className={`text-3xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {strategyDetail.name}
                      </h1>
                      <div className="flex gap-2">
                        {strategyDetail.isVerified && (
                          <Shield className="h-6 w-6 text-blue-500" />
                        )}
                        {strategyDetail.isPro && (
                          <Crown className="h-6 w-6 text-yellow-500" />
                        )}
                      </div>
                    </div>
                    <p className={`text-lg ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'} mb-3`}>
                      by {strategyDetail.developer}
                    </p>
                    <p className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'} leading-relaxed`}>
                      {strategyDetail.description}
                    </p>
                    
                    <div className="flex flex-wrap gap-2 mt-4">
                      <Badge variant="outline" className={getRiskColor(strategyDetail.riskLevel)}>
                        {strategyDetail.riskLevel.toUpperCase()} RISK
                      </Badge>
                      <Badge variant="outline">{strategyDetail.category}</Badge>
                      <Badge variant="outline">{strategyDetail.assetType}</Badge>
                      <Badge variant="secondary">v{strategyDetail.version}</Badge>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-3">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsLiked(!isLiked)}
                        className="flex items-center gap-1"
                      >
                        <Heart className={`h-4 w-4 ${isLiked ? 'fill-current text-red-500' : ''}`} />
                        {isLiked ? 'Liked' : 'Like'}
                      </Button>
                      <Button variant="outline" size="sm" className="flex items-center gap-1">
                        <Share2 className="h-4 w-4" />
                        Share
                      </Button>
                      <Button variant="outline" size="sm" className="flex items-center gap-1">
                        <Flag className="h-4 w-4" />
                        Report
                      </Button>
                    </div>
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Performance Overview */}
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Performance Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
                  <div className="text-center">
                    <div className={`text-3xl font-bold mb-1 ${strategyDetail.roi > 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {strategyDetail.roi > 0 ? '+' : ''}{strategyDetail.roi.toFixed(1)}%
                    </div>
                    <div className="flex items-center justify-center gap-1 mb-1">
                      {strategyDetail.roiChange > 0 ? (
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500" />
                      )}
                      <span className={`text-sm ${strategyDetail.roiChange > 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {strategyDetail.roiChange > 0 ? '+' : ''}{strategyDetail.roiChange.toFixed(1)}%
                      </span>
                    </div>
                    <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      Total Return
                    </span>
                  </div>
                  
                  <div className="text-center">
                    <div className={`text-3xl font-bold mb-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {strategyDetail.backtestResults.sharpeRatio.toFixed(1)}
                    </div>
                    <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      Sharpe Ratio
                    </span>
                  </div>
                  
                  <div className="text-center">
                    <div className={`text-3xl font-bold mb-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {strategyDetail.backtestResults.winRate.toFixed(0)}%
                    </div>
                    <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      Win Rate
                    </span>
                  </div>
                  
                  <div className="text-center">
                    <div className={`text-3xl font-bold mb-1 text-red-500`}>
                      {strategyDetail.backtestResults.maxDrawdown.toFixed(1)}%
                    </div>
                    <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      Max Drawdown
                    </span>
                  </div>
                </div>
                
                <PerformanceChart />
              </CardContent>
            </Card>

            {/* Detailed Content Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="backtest">Backtest</TabsTrigger>
                <TabsTrigger value="reviews">Reviews</TabsTrigger>
                <TabsTrigger value="docs">Docs</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-6 mt-6">
                <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <CardHeader>
                    <CardTitle>About This Strategy</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose dark:prose-invert max-w-none">
                      {strategyDetail.longDescription.split('\n\n').map((paragraph, index) => (
                        <p key={index} className={`mb-4 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <CardHeader>
                    <CardTitle>Supported Trading Pairs</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {strategyDetail.tradingPairs.map((pair) => (
                        <Badge key={pair} variant="secondary" className="text-sm">
                          {pair}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <CardHeader>
                    <CardTitle>Features</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {strategyDetail.features.map((feature, index) => (
                        <div key={index} className="flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                            {feature}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="backtest" className="mt-6">
                <BacktestResults results={strategyDetail.backtestResults} />
              </TabsContent>

              <TabsContent value="reviews" className="mt-6">
                <ReviewSection strategyId={strategyDetail.id} rating={strategyDetail.rating} reviewCount={strategyDetail.reviews} />
              </TabsContent>

              <TabsContent value="docs" className="mt-6">
                <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <CardHeader>
                    <CardTitle>Documentation & Resources</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Button variant="outline" className="justify-start h-12">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Setup Guide
                      </Button>
                      <Button variant="outline" className="justify-start h-12">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        API Documentation
                      </Button>
                      <Button variant="outline" className="justify-start h-12">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Video Tutorials
                      </Button>
                      <Button variant="outline" className="justify-start h-12">
                        <ExternalLink className="h-4 w-4 mr-2" />
                        FAQs
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Purchase Card */}
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} sticky top-24`}>
              <CardHeader>
                <div className="text-center">
                  <div className={`text-3xl font-bold mb-2 ${strategyDetail.price === 'free' ? 'text-green-500' : theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                    ${strategyDetail.price}/month
                  </div>
                  <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    30-day money back guarantee
                  </p>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button 
                  className="w-full bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-semibold h-12 text-lg"
                >
                  <Play className="h-5 w-5 mr-2" />
                  Plug In Strategy
                  <ChevronRight className="h-5 w-5 ml-2" />
                </Button>
                
                <div className="space-y-2">
                  <Button variant="outline" className="w-full">
                    <Activity className="h-4 w-4 mr-2" />
                    Paper Trade First
                  </Button>
                  <Button variant="outline" className="w-full">
                    <Settings className="h-4 w-4 mr-2" />
                    Customize Settings
                  </Button>
                </div>

                <div className={`text-center p-3 rounded-lg ${theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'}`}>
                  <div className="flex items-center justify-center gap-1 text-green-500 mb-1">
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">Risk-Free Trial</span>
                  </div>
                  <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    Test with paper trading before going live
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Strategy Stats */}
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <CardHeader>
                <CardTitle className="text-lg">Strategy Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Star className="h-4 w-4 text-yellow-500 fill-current" />
                    <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {strategyDetail.rating.toFixed(1)}
                    </span>
                  </div>
                  <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    ({strategyDetail.reviews} reviews)
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Download className="h-4 w-4 text-blue-500" />
                    <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {strategyDetail.downloads.toLocaleString()}
                    </span>
                  </div>
                  <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    total downloads
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-green-500" />
                    <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {Math.floor(strategyDetail.downloads * 0.7)}
                    </span>
                  </div>
                  <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    active users
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-purple-500" />
                    <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {new Date(strategyDetail.lastUpdated).toLocaleDateString()}
                    </span>
                  </div>
                  <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    last updated
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Requirements */}
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  Requirements
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {Object.entries(strategyDetail.requirements).map(([key, value]) => (
                  <div key={key} className="flex flex-col">
                    <span className={`text-sm font-medium capitalize ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                      {key.replace(/([A-Z])/g, ' $1')}
                    </span>
                    <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      {value}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Developer Info */}
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <CardHeader>
                <CardTitle className="text-lg">Developer</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                    {strategyDetail.developer.substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h4 className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                      {strategyDetail.developer}
                    </h4>
                    <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      Verified Developer
                    </p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Button variant="outline" className="w-full justify-start" size="sm">
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Contact Developer
                  </Button>
                  <Button variant="outline" className="w-full justify-start" size="sm">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View Profile
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}