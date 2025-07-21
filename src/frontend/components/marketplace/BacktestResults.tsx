'use client';

import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, TrendingDown, Calendar, DollarSign, Target, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import { useTheme } from 'next-themes';

interface BacktestResultsProps {
  results: {
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    avgTrade: number;
    profitFactor: number;
    totalTrades: number;
    avgHoldingTime: string;
  };
}

// Mock detailed backtest data
const monthlyReturns = [
  { month: 'Jan 23', return: 8.5, benchmark: 3.2 },
  { month: 'Feb 23', return: 6.7, benchmark: 2.6 },
  { month: 'Mar 23', return: -2.4, benchmark: -1.3 },
  { month: 'Apr 23', return: 7.8, benchmark: 4.2 },
  { month: 'May 23', return: 9.8, benchmark: 2.3 },
  { month: 'Jun 23', return: 12.8, benchmark: 3.3 },
  { month: 'Jul 23', return: 6.7, benchmark: 2.6 },
  { month: 'Aug 23', return: -3.2, benchmark: -0.8 },
  { month: 'Sep 23', return: 16.8, benchmark: 3.5 },
  { month: 'Oct 23', return: 12.6, benchmark: 2.4 },
  { month: 'Nov 23', return: 14.3, benchmark: 3.3 },
  { month: 'Dec 23', return: 12.8, benchmark: 3.4 }
];

const tradeDistribution = [
  { name: 'Winning Trades', value: 67.2, color: '#10b981' },
  { name: 'Losing Trades', value: 32.8, color: '#ef4444' }
];

const riskMetrics = [
  { metric: 'Value at Risk (95%)', value: '-4.2%', status: 'good' },
  { metric: 'Expected Shortfall', value: '-6.8%', status: 'good' },
  { metric: 'Beta vs Market', value: '0.85', status: 'good' },
  { metric: 'Correlation with BTC', value: '0.72', status: 'neutral' },
  { metric: 'Maximum Daily Loss', value: '-8.1%', status: 'warning' },
  { metric: 'Volatility (Annualized)', value: '18.5%', status: 'neutral' }
];

const BacktestResults: React.FC<BacktestResultsProps> = ({ results }) => {
  const { theme } = useTheme();
  const [selectedPeriod, setSelectedPeriod] = useState('1Y');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'bad': return 'text-red-500';
      default: return theme === 'dark' ? 'text-gray-400' : 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'bad': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default: return null;
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className={`p-3 rounded-lg shadow-lg border ${
          theme === 'dark' 
            ? 'bg-gray-800 border-gray-700 text-white' 
            : 'bg-white border-gray-200 text-gray-900'
        }`}>
          <p className="font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.dataKey === 'return' ? 'Strategy' : 'Benchmark'}: {entry.value.toFixed(1)}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <TrendingUp className="h-5 w-5 text-green-500 mr-2" />
              <span className="text-2xl font-bold text-green-500">
                +{results.totalReturn.toFixed(1)}%
              </span>
            </div>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Total Return
            </p>
          </CardContent>
        </Card>

        <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <Target className="h-5 w-5 text-blue-500 mr-2" />
              <span className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                {results.sharpeRatio.toFixed(1)}
              </span>
            </div>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Sharpe Ratio
            </p>
          </CardContent>
        </Card>

        <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <TrendingDown className="h-5 w-5 text-red-500 mr-2" />
              <span className="text-2xl font-bold text-red-500">
                {results.maxDrawdown.toFixed(1)}%
              </span>
            </div>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Max Drawdown
            </p>
          </CardContent>
        </Card>

        <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <CheckCircle className="h-5 w-5 text-purple-500 mr-2" />
              <span className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                {results.winRate.toFixed(0)}%
              </span>
            </div>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Win Rate
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="performance" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="trades">Trade Analysis</TabsTrigger>
          <TabsTrigger value="risk">Risk Metrics</TabsTrigger>
          <TabsTrigger value="periods">Time Periods</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-6 mt-6">
          <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Monthly Returns Comparison</CardTitle>
              <div className="flex gap-2">
                {['6M', '1Y', '2Y'].map((period) => (
                  <Button
                    key={period}
                    variant={selectedPeriod === period ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedPeriod(period)}
                  >
                    {period}
                  </Button>
                ))}
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthlyReturns}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#374151' : '#e5e7eb'} />
                    <XAxis 
                      dataKey="month" 
                      stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
                      fontSize={12}
                    />
                    <YAxis 
                      stroke={theme === 'dark' ? '#9ca3af' : '#6b7280'}
                      fontSize={12}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="return" fill="#10b981" name="Strategy" radius={[2, 2, 0, 0]} />
                    <Bar dataKey="benchmark" fill="#6b7280" name="Benchmark" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <CardHeader>
                <CardTitle>Additional Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    Profit Factor
                  </span>
                  <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                    {results.profitFactor.toFixed(1)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    Average Trade
                  </span>
                  <span className={`font-semibold ${results.avgTrade > 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {results.avgTrade > 0 ? '+' : ''}{results.avgTrade.toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    Total Trades
                  </span>
                  <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                    {results.totalTrades.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    Avg Holding Time
                  </span>
                  <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                    {results.avgHoldingTime}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
              <CardHeader>
                <CardTitle>Trade Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-48 flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={tradeDistribution}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {tradeDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value: number) => [`${value.toFixed(1)}%`, '']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      Winning ({results.winRate.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      Losing ({(100 - results.winRate).toFixed(0)}%)
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trades" className="space-y-6 mt-6">
          <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <CardHeader>
              <CardTitle>Trade Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className={`text-2xl font-bold text-green-500 mb-1`}>
                    {Math.round(results.totalTrades * (results.winRate / 100))}
                  </div>
                  <div className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    Winning Trades
                  </div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold text-red-500 mb-1`}>
                    {Math.round(results.totalTrades * ((100 - results.winRate) / 100))}
                  </div>
                  <div className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    Losing Trades
                  </div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold text-blue-500 mb-1`}>
                    +8.7%
                  </div>
                  <div className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    Avg Winner
                  </div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold text-orange-500 mb-1`}>
                    -3.2%
                  </div>
                  <div className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    Avg Loser
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="risk" className="space-y-6 mt-6">
          <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <CardHeader>
              <CardTitle>Risk Assessment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {riskMetrics.map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(item.status)}
                      <span className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                        {item.metric}
                      </span>
                    </div>
                    <span className={`font-semibold ${getStatusColor(item.status)}`}>
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="periods" className="space-y-6 mt-6">
          <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <CardHeader>
              <CardTitle>Performance by Time Period</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { period: 'Last 30 Days', return: 12.3, trades: 47, winRate: 68.1 },
                  { period: 'Last 90 Days', return: 31.7, trades: 142, winRate: 66.9 },
                  { period: 'Last 6 Months', return: 78.4, trades: 284, winRate: 67.8 },
                  { period: 'Last 12 Months', return: 142.5, trades: 568, winRate: 67.2 }
                ].map((period, index) => (
                  <div key={index} className="grid grid-cols-4 gap-4 p-4 rounded-lg bg-gray-50 dark:bg-gray-700">
                    <div>
                      <div className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {period.period}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className={`font-bold ${period.return > 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {period.return > 0 ? '+' : ''}{period.return.toFixed(1)}%
                      </div>
                      <div className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                        Return
                      </div>
                    </div>
                    <div className="text-center">
                      <div className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {period.trades}
                      </div>
                      <div className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                        Trades
                      </div>
                    </div>
                    <div className="text-center">
                      <div className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {period.winRate.toFixed(0)}%
                      </div>
                      <div className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                        Win Rate
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BacktestResults;