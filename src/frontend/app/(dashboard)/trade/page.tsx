'use client';

import React, { useState, useEffect } from 'react';

import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  BarChart3, 
  Settings,
  Play,
  Pause,
  AlertCircle,
  CheckCircle,
  Clock,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';

interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  status: 'active' | 'pending' | 'closed';
}

interface Strategy {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'stopped';
  pnl: number;
  pnlPercent: number;
  winRate: number;
  totalTrades: number;
}

export default function Trade() {
  
  const [mounted, setMounted] = useState(false);
  const [selectedTab, setSelectedTab] = useState('overview');
  useEffect(() => {
    setMounted(true);
  }, []);

  // Avoid hydration mismatch
  if (!mounted) return null;

  // Mock data
  const positions: Position[] = [
    {
      id: '1',
      symbol: 'BTC/USDT',
      side: 'long',
      size: 0.5,
      entryPrice: 42150,
      currentPrice: 43200,
      pnl: 525,
      pnlPercent: 2.49,
      status: 'active'
    },
    {
      id: '2',
      symbol: 'ETH/USDT',
      side: 'short',
      size: 2.1,
      entryPrice: 2850,
      currentPrice: 2820,
      pnl: 63,
      pnlPercent: 1.05,
      status: 'active'
    }
  ];

  const strategies: Strategy[] = [
    {
      id: '1',
      name: 'Quantum Momentum Pro',
      status: 'active',
      pnl: 1247.5,
      pnlPercent: 12.3,
      winRate: 68.2,
      totalTrades: 47
    },
    {
      id: '2',
      name: 'AI Grid Trading Bot',
      status: 'paused',
      pnl: -123.8,
      pnlPercent: -2.1,
      winRate: 59.1,
      totalTrades: 22
    }
  ];

  const totalPortfolio = {
    balance: 15420.75,
    pnl: 1672.3,
    pnlPercent: 12.17,
    positions: positions.length,
    activeStrategies: strategies.filter(s => s.status === 'active').length
  };

  return (
    <div className="space-y-6">
      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className={"bg-white border-gray-200 shadow-lg transition-all hover:shadow-xl dark:bg-slate-800 dark:border-slate-700 dark:shadow-xl"}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={"text-sm font-medium text-gray-600 dark:text-slate-400"}>
                  Total Balance
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="p-2 rounded-lg bg-yellow-500/10">
                    <DollarSign className="h-4 w-4 text-yellow-500" />
                  </div>
                  <span className={"text-2xl font-bold text-gray-900 dark:text-white"}>
                    ${totalPortfolio.balance.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={"bg-white border-gray-200 shadow-lg transition-all hover:shadow-xl dark:bg-slate-800 dark:border-slate-700 dark:shadow-xl"}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={"text-sm font-medium text-gray-600 dark:text-slate-400"}>
                  Total P&L
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <div className={`p-2 rounded-lg ${totalPortfolio.pnl > 0 ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                    {totalPortfolio.pnl > 0 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                  </div>
                  <span className={`text-2xl font-bold ${totalPortfolio.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {totalPortfolio.pnl > 0 ? '+' : ''}${totalPortfolio.pnl.toFixed(2)}
                  </span>
                </div>
                <span className={`text-sm ${totalPortfolio.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {totalPortfolio.pnl > 0 ? '+' : ''}{totalPortfolio.pnlPercent.toFixed(2)}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={"bg-white border-gray-200 shadow-lg transition-all hover:shadow-xl dark:bg-slate-800 dark:border-slate-700 dark:shadow-xl"}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={"text-sm font-medium text-gray-600 dark:text-slate-400"}>
                  Active Positions
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <Activity className="h-4 w-4 text-blue-500" />
                  </div>
                  <span className={"text-2xl font-bold text-gray-900 dark:text-white"}>
                    {totalPortfolio.positions}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={"bg-white border-gray-200 shadow-lg transition-all hover:shadow-xl dark:bg-slate-800 dark:border-slate-700 dark:shadow-xl"}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={"text-sm font-medium text-gray-600 dark:text-slate-400"}>
                  Active Strategies
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="p-2 rounded-lg bg-yellow-500/10">
                    <Zap className="h-4 w-4 text-yellow-500" />
                  </div>
                  <span className={"text-2xl font-bold text-gray-900 dark:text-white"}>
                    {totalPortfolio.activeStrategies}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Trading Interface */}
      <Card className="bg-white border-gray-200 shadow-lg dark:bg-slate-800 dark:border-slate-700 dark:shadow-xl">
        <CardHeader className="pb-0">
          <Tabs value={selectedTab} onValueChange={setSelectedTab}>
            <TabsList className="grid w-full grid-cols-3 bg-gray-100 p-1 rounded-lg dark:bg-slate-700">
              <TabsTrigger 
                value="overview"
                className="font-medium transition-all data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm dark:data-[state=active]:bg-slate-600 dark:data-[state=active]:text-white"
              >
                Overview
              </TabsTrigger>
              <TabsTrigger 
                value="positions"
                className="font-medium transition-all data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm dark:data-[state=active]:bg-slate-600 dark:data-[state=active]:text-white"
              >
                Positions
              </TabsTrigger>
              <TabsTrigger 
                value="strategies"
                className="font-medium transition-all data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm dark:data-[state=active]:bg-slate-600 dark:data-[state=active]:text-white"
              >
                Strategies
              </TabsTrigger>
            </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Active Positions */}
            <div className="p-6 rounded-lg bg-gray-50 border border-gray-200 dark:bg-slate-700/50 dark:border-slate-600">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-2 rounded-lg bg-blue-500/10">
                  <Activity className="h-5 w-5 text-blue-500" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Active Positions
                </h3>
              </div>
              <div className="space-y-4">
                {positions.map((position) => (
                  <div key={position.id} className="p-4 rounded-lg bg-white border border-gray-200 transition-all hover:shadow-md dark:bg-slate-600/50 dark:border-slate-500">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-900 dark:text-white">
                          {position.symbol}
                        </span>
                        <Badge 
                          variant={position.side === 'long' ? 'default' : 'secondary'}
                          className={position.side === 'long' ? 'bg-green-500' : 'bg-red-500'}
                        >
                          {position.side.toUpperCase()}
                        </Badge>
                      </div>
                      <span className={`font-bold ${position.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {position.pnl > 0 ? '+' : ''}${position.pnl.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-slate-400">
                        Size: {position.size}
                      </span>
                      <span className="text-gray-600 dark:text-slate-400">
                        Entry: ${position.entryPrice.toLocaleString()}
                      </span>
                      <span className="text-gray-600 dark:text-slate-400">
                        Current: ${position.currentPrice.toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Strategy Performance */}
            <div className="p-6 rounded-lg bg-gray-50 border border-gray-200 dark:bg-slate-700/50 dark:border-slate-600">
              <div className="flex items-center gap-2 mb-4">
                <div className="p-2 rounded-lg bg-yellow-500/10">
                  <BarChart3 className="h-5 w-5 text-yellow-500" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Strategy Performance
                </h3>
              </div>
              <div className="space-y-4">
                {strategies.map((strategy) => (
                  <div key={strategy.id} className="p-4 rounded-lg bg-white border border-gray-200 transition-all hover:shadow-md dark:bg-slate-600/50 dark:border-slate-500">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-900 dark:text-white">
                          {strategy.name}
                        </span>
                        <div className="flex items-center gap-1">
                          {strategy.status === 'active' ? (
                            <Play className="h-3 w-3 text-green-500" />
                          ) : (
                            <Pause className="h-3 w-3 text-yellow-500" />
                          )}
                          <Badge 
                            variant={strategy.status === 'active' ? 'default' : 'secondary'}
                            className={strategy.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'}
                          >
                            {strategy.status}
                          </Badge>
                        </div>
                      </div>
                      <span className={`font-bold ${strategy.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {strategy.pnl > 0 ? '+' : ''}${strategy.pnl.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-slate-400">
                        Win Rate: {strategy.winRate.toFixed(1)}%
                      </span>
                      <span className="text-gray-600 dark:text-slate-400">
                        Trades: {strategy.totalTrades}
                      </span>
                      <span className={`${strategy.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {strategy.pnl > 0 ? '+' : ''}{strategy.pnlPercent.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="positions" className="space-y-6 mt-6">
          <div className="p-6 rounded-lg bg-gray-50 border border-gray-200 dark:bg-slate-700/50 dark:border-slate-600">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-blue-500/10">
                  <Activity className="h-5 w-5 text-blue-500" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">All Positions</h3>
              </div>
              <Button className="bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-semibold">
                New Position
              </Button>
            </div>
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-slate-600">
                      <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-slate-300">Symbol</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-slate-300">Side</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-slate-300">Size</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-slate-300">Entry Price</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-slate-300">Current Price</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-slate-300">P&L</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-700 dark:text-slate-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((position) => (
                      <tr key={position.id} className="border-b border-gray-200 hover:bg-gray-100 transition-colors dark:border-slate-600 dark:hover:bg-slate-600/30">
                        <td className="py-3 px-4">
                          <span className="font-semibold text-gray-900 dark:text-white">
                            {position.symbol}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <Badge 
                            variant={position.side === 'long' ? 'default' : 'secondary'}
                            className={position.side === 'long' ? 'bg-green-500' : 'bg-red-500'}
                          >
                            {position.side.toUpperCase()}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-gray-700 dark:text-slate-300">
                          {position.size}
                        </td>
                        <td className="py-3 px-4 text-gray-700 dark:text-slate-300">
                          ${position.entryPrice.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-gray-700 dark:text-slate-300">
                          ${position.currentPrice.toLocaleString()}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex flex-col">
                            <span className={`font-bold ${position.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                              {position.pnl > 0 ? '+' : ''}${position.pnl.toFixed(2)}
                            </span>
                            <span className={`text-xs ${position.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                              {position.pnl > 0 ? '+' : ''}{position.pnlPercent.toFixed(2)}%
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm">
                              Edit
                            </Button>
                            <Button variant="outline" size="sm" className="text-red-500 hover:text-red-600">
                              Close
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="strategies" className="space-y-6 mt-6">
          <div className="p-6 rounded-lg bg-gray-50 border border-gray-200 dark:bg-slate-700/50 dark:border-slate-600">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-yellow-500/10">
                  <BarChart3 className="h-5 w-5 text-yellow-500" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Trading Strategies</h3>
              </div>
              <Button 
                className="bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-semibold"
                onClick={() => window.open('/marketplace', '_blank')}
              >
                Browse Marketplace
              </Button>
            </div>
            <div className="space-y-4">
              {strategies.map((strategy) => (
                <div key={strategy.id} className="p-6 rounded-lg border bg-white border-gray-200 transition-all hover:shadow-md dark:bg-slate-600/50 dark:border-slate-500">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {strategy.name}
                      </h3>
                      <Badge 
                        variant={strategy.status === 'active' ? 'default' : 'secondary'}
                        className={strategy.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'}
                      >
                        {strategy.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Settings className="h-4 w-4" />
                        Settings
                      </Button>
                      {strategy.status === 'active' ? (
                        <Button variant="outline" size="sm">
                          <Pause className="h-4 w-4" />
                          Pause
                        </Button>
                      ) : (
                        <Button className="bg-green-500 hover:bg-green-600" size="sm">
                          <Play className="h-4 w-4" />
                          Start
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-slate-400">Total P&L</p>
                      <p className={`text-lg font-bold ${strategy.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {strategy.pnl > 0 ? '+' : ''}${strategy.pnl.toFixed(2)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-slate-400">Return %</p>
                      <p className={`text-lg font-bold ${strategy.pnl > 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {strategy.pnl > 0 ? '+' : ''}{strategy.pnlPercent.toFixed(2)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-slate-400">Win Rate</p>
                      <p className="text-lg font-bold text-gray-900 dark:text-white">
                        {strategy.winRate.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-slate-400">Total Trades</p>
                      <p className="text-lg font-bold text-gray-900 dark:text-white">
                        {strategy.totalTrades}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Progress 
                      value={strategy.winRate} 
                      className="flex-1 h-2"
                    />
                    <span className="text-sm text-gray-600 dark:text-slate-400">
                      Performance Score
                    </span>
                  </div>
                </div>
              ))}
              
              <div className="p-6 rounded-lg border-2 border-dashed border-gray-300 bg-gray-100/50 dark:border-slate-500 dark:bg-slate-600/30 text-center">
                <div className="flex flex-col items-center gap-3">
                  <div className="p-3 rounded-full bg-gray-200 dark:bg-slate-600">
                    <BarChart3 className="h-6 w-6 text-gray-500 dark:text-slate-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      No Strategies Running
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-slate-400 mt-1">
                      Browse our marketplace to find AI-powered trading strategies
                    </p>
                  </div>
                  <Button 
                    className="bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-semibold"
                    onClick={() => window.open('/marketplace', '_blank')}
                  >
                    Explore Strategies
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>
          </Tabs>
        </CardHeader>
      </Card>
    </div>
  );
}