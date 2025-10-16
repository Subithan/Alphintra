import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Button } from '@/components/ui/no-code/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/no-code/tabs';
import { 
  TrendingUp, 
  TrendingDown,
  BarChart3,
  PieChart,
  LineChart,
  Target,
  Shield,
  DollarSign,
  Percent,
  Activity,
  Calendar,
  Download,
  Filter,
  RefreshCw,
  Settings,
  Maximize2,
  AlertTriangle,
  CheckCircle,
  Clock,
  Users,
  Briefcase,
  Globe,
  Pause
} from 'lucide-react';
import {
  PortfolioOrchestrator,
  PortfolioState,
  StrategyContribution,
  AttributionAnalysis
} from '@/lib/portfolio-orchestrator';
import {
  AdvancedRiskManager,
  RiskMetrics
} from '@/lib/advanced-risk-manager';

interface PortfolioAnalyticsDashboardProps {
  portfolioOrchestrator: PortfolioOrchestrator;
  riskManager: AdvancedRiskManager;
  timeRange: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL';
  onTimeRangeChange: (range: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL') => void;
}

interface PerformanceMetrics {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  sortinoRatio: number;
  calmarRatio: number;
  maxDrawdown: number;
  currentDrawdown: number;
  winRate: number;
  profitFactor: number;
  var95: number;
  expectedShortfall: number;
  beta: number;
  alpha: number;
  informationRatio: number;
  trackingError: number;
}

interface AllocationData {
  strategy_id: string;
  strategy_name: string;
  allocation: number;
  value: number;
  return_1d: number;
  return_1w: number;
  return_1m: number;
  volatility: number;
  sharpe_ratio: number;
  correlation: number;
  risk_contribution: number;
}

interface RiskAnalysis {
  portfolioRisk: number;
  concentrationRisk: number;
  correlationRisk: number;
  liquidityRisk: number;
  sectorRisks: Record<string, number>;
  geographicRisks: Record<string, number>;
  currencyRisks: Record<string, number>;
  stressTestResults: StressTestResult[];
}

interface StressTestResult {
  scenario: string;
  description: string;
  portfolioImpact: number;
  worstStrategy: string;
  worstImpact: number;
  confidence: number;
}

interface TimeSeriesData {
  timestamp: Date;
  portfolio_value: number;
  benchmark_value: number;
  drawdown: number;
  volatility: number;
  daily_return: number;
  cumulative_return: number;
}

export function PortfolioAnalyticsDashboard({
  portfolioOrchestrator,
  riskManager,
  timeRange,
  onTimeRangeChange
}: PortfolioAnalyticsDashboardProps) {
  const [portfolioState, setPortfolioState] = useState<PortfolioState | null>(null);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([]);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'performance' | 'risk' | 'allocation' | 'attribution'>('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    updateAnalyticsData();
    
    if (autoRefresh) {
      const interval = setInterval(updateAnalyticsData, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, timeRange]);

  const updateAnalyticsData = async () => {
    try {
      setIsLoading(true);
      
      const state = portfolioOrchestrator.getPortfolioState();
      const risk = riskManager.getRiskMetrics();
      
      setPortfolioState(state);
      setRiskMetrics(risk);
      
      // Generate time series data
      const series = generateTimeSeriesData(state, timeRange);
      setTimeSeriesData(series);
      
    } catch (error) {
      console.error('Error updating analytics data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateTimeSeriesData = (state: PortfolioState, range: string): TimeSeriesData[] => {
    // Simplified time series generation
    const days = range === '1D' ? 1 : range === '1W' ? 7 : range === '1M' ? 30 : 
                 range === '3M' ? 90 : range === '6M' ? 180 : range === '1Y' ? 365 : 1000;
    
    const data: TimeSeriesData[] = [];
    const baseValue = state.total_equity;
    
    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));
      
      const volatility = 0.15 + Math.random() * 0.1; // 15-25% volatility
      const dailyReturn = (Math.random() - 0.48) * volatility / Math.sqrt(252); // Slight positive bias
      const portfolioValue = baseValue * (1 + dailyReturn * i / days);
      const benchmarkValue = baseValue * (1 + 0.08 * i / 365); // 8% annual benchmark
      
      data.push({
        timestamp: date,
        portfolio_value: portfolioValue,
        benchmark_value: benchmarkValue,
        drawdown: Math.random() * 5, // 0-5% drawdown
        volatility: volatility * 100,
        daily_return: dailyReturn * 100,
        cumulative_return: ((portfolioValue - baseValue) / baseValue) * 100
      });
    }
    
    return data;
  };

  const performanceMetrics = useMemo((): PerformanceMetrics => {
    if (!portfolioState || !timeSeriesData.length) {
      return {
        totalReturn: 0,
        annualizedReturn: 0,
        volatility: 0,
        sharpeRatio: 0,
        sortinoRatio: 0,
        calmarRatio: 0,
        maxDrawdown: 0,
        currentDrawdown: 0,
        winRate: 0,
        profitFactor: 0,
        var95: 0,
        expectedShortfall: 0,
        beta: 1,
        alpha: 0,
        informationRatio: 0,
        trackingError: 0
      };
    }

    const returns = timeSeriesData.map(d => d.daily_return);
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const volatility = Math.sqrt(
      returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
    ) * Math.sqrt(252);

    const totalReturn = ((portfolioState.total_equity - 100000) / 100000) * 100; // Assuming 100k start
    const annualizedReturn = totalReturn * (365 / timeSeriesData.length);
    const sharpeRatio = volatility > 0 ? (annualizedReturn - 3) / volatility : 0; // 3% risk-free rate
    const maxDrawdown = Math.max(...timeSeriesData.map(d => d.drawdown));
    const currentDrawdown = timeSeriesData[timeSeriesData.length - 1]?.drawdown || 0;

    return {
      totalReturn,
      annualizedReturn,
      volatility,
      sharpeRatio,
      sortinoRatio: sharpeRatio * 1.2, // Approximation
      calmarRatio: maxDrawdown > 0 ? annualizedReturn / maxDrawdown : 0,
      maxDrawdown,
      currentDrawdown,
      winRate: returns.filter(r => r > 0).length / returns.length * 100,
      profitFactor: 1.5 + Math.random() * 0.5, // 1.5-2.0
      var95: Math.abs(returns.sort((a, b) => a - b)[Math.floor(returns.length * 0.05)] || 0),
      expectedShortfall: Math.abs(avgReturn) * 1.3,
      beta: 0.8 + Math.random() * 0.4, // 0.8-1.2
      alpha: annualizedReturn - 8, // vs 8% benchmark
      informationRatio: sharpeRatio * 0.8,
      trackingError: volatility * 0.6
    };
  }, [portfolioState, timeSeriesData]);

  const allocationData = useMemo((): AllocationData[] => {
    if (!portfolioState) return [];

    return Object.entries(portfolioState.performance_metrics.strategy_contributions).map(([id, contrib]) => ({
      strategy_id: id,
      strategy_name: `Strategy ${id.slice(0, 8)}`,
      allocation: contrib.allocation,
      value: portfolioState.total_equity * (contrib.allocation / 100),
      return_1d: contrib.individual_return * 0.1, // Approximate daily
      return_1w: contrib.individual_return * 0.7, // Approximate weekly  
      return_1m: contrib.individual_return,
      volatility: 15 + Math.random() * 10, // 15-25%
      sharpe_ratio: 0.5 + Math.random() * 1.5, // 0.5-2.0
      correlation: contrib.correlation_with_portfolio,
      risk_contribution: contrib.risk_contribution
    }));
  }, [portfolioState]);

  const riskAnalysis = useMemo((): RiskAnalysis => {
    if (!riskMetrics || !portfolioState) {
      return {
        portfolioRisk: 0,
        concentrationRisk: 0,
        correlationRisk: 0,
        liquidityRisk: 0,
        sectorRisks: {},
        geographicRisks: {},
        currencyRisks: {},
        stressTestResults: []
      };
    }

    return {
      portfolioRisk: riskMetrics.portfolio_risk * 100,
      concentrationRisk: riskMetrics.concentration_risk,
      correlationRisk: riskMetrics.correlation_risk * 100,
      liquidityRisk: 25 + Math.random() * 25, // 25-50%
      sectorRisks: {
        'Technology': 35,
        'Financial': 25,
        'Healthcare': 20,
        'Energy': 15,
        'Others': 5
      },
      geographicRisks: {
        'North America': 60,
        'Europe': 25,
        'Asia': 10,
        'Others': 5
      },
      currencyRisks: {
        'USD': 70,
        'EUR': 15,
        'GBP': 8,
        'JPY': 5,
        'Others': 2
      },
      stressTestResults: [
        {
          scenario: 'Market Crash (-20%)',
          description: '2008-style market correction',
          portfolioImpact: -15.2,
          worstStrategy: 'Growth Strategy',
          worstImpact: -28.5,
          confidence: 0.95
        },
        {
          scenario: 'Interest Rate Shock (+3%)',
          description: 'Rapid rate increase',
          portfolioImpact: -8.7,
          worstStrategy: 'Bond Strategy',
          worstImpact: -18.3,
          confidence: 0.90
        },
        {
          scenario: 'Volatility Spike (VIX > 50)',
          description: 'High market volatility',
          portfolioImpact: -12.1,
          worstStrategy: 'Short Vol Strategy',
          worstImpact: -35.2,
          confidence: 0.85
        }
      ]
    };
  }, [riskMetrics, portfolioState]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value: number, decimals = 2) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
  };

  const formatNumber = (value: number, decimals = 2) => {
    return value.toFixed(decimals);
  };

  const getChangeColor = (value: number) => {
    return value >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getRiskColor = (risk: number) => {
    if (risk < 20) return 'text-green-600';
    if (risk < 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Portfolio Value</p>
                <p className="text-2xl font-bold">{formatCurrency(portfolioState?.total_equity || 0)}</p>
                <p className={`text-sm ${getChangeColor(performanceMetrics.totalReturn)}`}>
                  {formatPercentage(performanceMetrics.totalReturn)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Annual Return</p>
                <p className="text-2xl font-bold">{formatPercentage(performanceMetrics.annualizedReturn)}</p>
                <p className="text-sm text-gray-500">vs {formatPercentage(8)} benchmark</p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Sharpe Ratio</p>
                <p className="text-2xl font-bold">{formatNumber(performanceMetrics.sharpeRatio)}</p>
                <p className="text-sm text-gray-500">Risk-adj return</p>
              </div>
              <Target className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Max Drawdown</p>
                <p className="text-2xl font-bold text-red-600">{formatPercentage(performanceMetrics.maxDrawdown)}</p>
                <p className="text-sm text-gray-500">Current: {formatPercentage(performanceMetrics.currentDrawdown)}</p>
              </div>
              <TrendingDown className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Portfolio Performance Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <LineChart className="h-5 w-5" />
              <span>Portfolio Performance</span>
            </div>
            <div className="flex items-center space-x-2">
              {(['1D', '1W', '1M', '3M', '6M', '1Y', 'ALL'] as const).map(range => (
                <Button
                  key={range}
                  size="sm"
                  variant={timeRange === range ? "default" : "outline"}
                  onClick={() => onTimeRangeChange(range)}
                >
                  {range}
                </Button>
              ))}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            {/* Simplified chart representation */}
            <div className="w-full h-full bg-gradient-to-r from-blue-50 to-green-50 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
              <div className="text-center">
                <LineChart className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600">Portfolio Performance Chart</p>
                <p className="text-sm text-gray-500 mt-2">
                  {timeSeriesData.length} data points for {timeRange} period
                </p>
                <p className="text-sm text-gray-500">
                  Return: {formatPercentage(performanceMetrics.totalReturn)} | 
                  Volatility: {formatPercentage(performanceMetrics.volatility)}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Risk Metrics</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Portfolio Risk</span>
                <span className={getRiskColor(riskAnalysis.portfolioRisk)}>
                  {formatPercentage(riskAnalysis.portfolioRisk)}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Value at Risk (95%)</span>
                <span>{formatPercentage(performanceMetrics.var95)}</span>
              </div>
              <div className="flex justify-between">
                <span>Beta</span>
                <span>{formatNumber(performanceMetrics.beta)}</span>
              </div>
              <div className="flex justify-between">
                <span>Correlation Risk</span>
                <span className={getRiskColor(riskAnalysis.correlationRisk)}>
                  {formatPercentage(riskAnalysis.correlationRisk)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <PieChart className="h-5 w-5" />
              <span>Allocation</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {allocationData.slice(0, 4).map(strategy => (
                <div key={strategy.strategy_id} className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium">{strategy.strategy_name}</p>
                    <p className="text-xs text-gray-500">{formatCurrency(strategy.value)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">{formatPercentage(strategy.allocation)}</p>
                    <p className={`text-xs ${getChangeColor(strategy.return_1d)}`}>
                      {formatPercentage(strategy.return_1d)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Globe className="h-5 w-5" />
              <span>Diversification</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600 mb-2">Sector Exposure</p>
                {Object.entries(riskAnalysis.sectorRisks).slice(0, 3).map(([sector, risk]) => (
                  <div key={sector} className="flex justify-between text-sm">
                    <span>{sector}</span>
                    <span>{formatPercentage(risk)}</span>
                  </div>
                ))}
              </div>
              <div className="pt-2 border-t">
                <p className="text-sm text-gray-600 mb-2">Geographic Exposure</p>
                {Object.entries(riskAnalysis.geographicRisks).slice(0, 2).map(([region, risk]) => (
                  <div key={region} className="flex justify-between text-sm">
                    <span>{region}</span>
                    <span>{formatPercentage(risk)}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderPerformanceTab = () => (
    <div className="space-y-6">
      {/* Performance Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Total Return</p>
              <p className={`text-3xl font-bold ${getChangeColor(performanceMetrics.totalReturn)}`}>
                {formatPercentage(performanceMetrics.totalReturn)}
              </p>
              <p className="text-sm text-gray-500">Since inception</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Annualized Return</p>
              <p className={`text-3xl font-bold ${getChangeColor(performanceMetrics.annualizedReturn)}`}>
                {formatPercentage(performanceMetrics.annualizedReturn)}
              </p>
              <p className="text-sm text-gray-500">vs {formatPercentage(8)} benchmark</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Volatility</p>
              <p className="text-3xl font-bold text-blue-600">
                {formatPercentage(performanceMetrics.volatility)}
              </p>
              <p className="text-sm text-gray-500">Annualized</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Sharpe Ratio</p>
              <p className="text-3xl font-bold text-purple-600">
                {formatNumber(performanceMetrics.sharpeRatio)}
              </p>
              <p className="text-sm text-gray-500">Risk-adjusted</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Max Drawdown</p>
              <p className="text-3xl font-bold text-red-600">
                {formatPercentage(performanceMetrics.maxDrawdown)}
              </p>
              <p className="text-sm text-gray-500">Historical worst</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Win Rate</p>
              <p className="text-3xl font-bold text-green-600">
                {formatPercentage(performanceMetrics.winRate)}
              </p>
              <p className="text-sm text-gray-500">Winning periods</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Advanced Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Advanced Performance Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-3">Risk-Adjusted Returns</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Sortino Ratio</span>
                  <span className="font-medium">{formatNumber(performanceMetrics.sortinoRatio)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Calmar Ratio</span>
                  <span className="font-medium">{formatNumber(performanceMetrics.calmarRatio)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Information Ratio</span>
                  <span className="font-medium">{formatNumber(performanceMetrics.informationRatio)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Profit Factor</span>
                  <span className="font-medium">{formatNumber(performanceMetrics.profitFactor)}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-3">Market Relative</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Alpha</span>
                  <span className={`font-medium ${getChangeColor(performanceMetrics.alpha)}`}>
                    {formatPercentage(performanceMetrics.alpha)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Beta</span>
                  <span className="font-medium">{formatNumber(performanceMetrics.beta)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tracking Error</span>
                  <span className="font-medium">{formatPercentage(performanceMetrics.trackingError)}</span>
                </div>
                <div className="flex justify-between">
                  <span>R-Squared</span>
                  <span className="font-medium">{formatPercentage(85.5)}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Returns Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Returns Distribution</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-gradient-to-r from-red-50 via-yellow-50 to-green-50 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">Returns Distribution Histogram</p>
              <p className="text-sm text-gray-500 mt-2">
                Mean: {formatPercentage(performanceMetrics.annualizedReturn / 252)} daily | 
                Std: {formatPercentage(performanceMetrics.volatility / Math.sqrt(252))}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderRiskTab = () => (
    <div className="space-y-6">
      {/* Risk Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Portfolio Risk</p>
              <p className={`text-3xl font-bold ${getRiskColor(riskAnalysis.portfolioRisk)}`}>
                {formatPercentage(riskAnalysis.portfolioRisk)}
              </p>
              <p className="text-sm text-gray-500">Overall exposure</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Concentration Risk</p>
              <p className={`text-3xl font-bold ${getRiskColor(riskAnalysis.concentrationRisk)}`}>
                {formatPercentage(riskAnalysis.concentrationRisk)}
              </p>
              <p className="text-sm text-gray-500">Position sizing</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Correlation Risk</p>
              <p className={`text-3xl font-bold ${getRiskColor(riskAnalysis.correlationRisk)}`}>
                {formatPercentage(riskAnalysis.correlationRisk)}
              </p>
              <p className="text-sm text-gray-500">Strategy correlation</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Liquidity Risk</p>
              <p className={`text-3xl font-bold ${getRiskColor(riskAnalysis.liquidityRisk)}`}>
                {formatPercentage(riskAnalysis.liquidityRisk)}
              </p>
              <p className="text-sm text-gray-500">Exit difficulty</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* VaR Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Value at Risk Analysis</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">1-Day VaR (95%)</p>
              <p className="text-2xl font-bold text-red-600">
                {formatCurrency(riskMetrics?.var_1d || 0)}
              </p>
              <p className="text-xs text-gray-500">Max expected loss</p>
            </div>
            
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">5-Day VaR (95%)</p>
              <p className="text-2xl font-bold text-red-600">
                {formatCurrency(riskMetrics?.var_5d || 0)}
              </p>
              <p className="text-xs text-gray-500">Weekly risk</p>
            </div>
            
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">Expected Shortfall</p>
              <p className="text-2xl font-bold text-red-600">
                {formatCurrency(riskMetrics?.expected_shortfall || 0)}
              </p>
              <p className="text-xs text-gray-500">Tail risk</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Sector Risk Exposure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(riskAnalysis.sectorRisks).map(([sector, risk]) => (
                <div key={sector}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">{sector}</span>
                    <span className="text-sm">{formatPercentage(risk)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getRiskColor(risk).includes('green') ? 'bg-green-500' : 
                        getRiskColor(risk).includes('yellow') ? 'bg-yellow-500' : 'bg-red-500'}`}
                      style={{ width: `${Math.min(100, risk)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Geographic Risk Exposure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(riskAnalysis.geographicRisks).map(([region, risk]) => (
                <div key={region}>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">{region}</span>
                    <span className="text-sm">{formatPercentage(risk)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getRiskColor(risk).includes('green') ? 'bg-green-500' : 
                        getRiskColor(risk).includes('yellow') ? 'bg-yellow-500' : 'bg-red-500'}`}
                      style={{ width: `${Math.min(100, risk)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Stress Testing */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5" />
            <span>Stress Test Results</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {riskAnalysis.stressTestResults.map(test => (
              <div key={test.scenario} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{test.scenario}</h4>
                  <Badge className={`${
                    Math.abs(test.portfolioImpact) < 10 ? 'bg-green-100 text-green-800' :
                    Math.abs(test.portfolioImpact) < 20 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {formatPercentage(test.portfolioImpact)}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600 mb-3">{test.description}</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Portfolio Impact</p>
                    <p className="font-medium text-red-600">{formatPercentage(test.portfolioImpact)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Worst Strategy</p>
                    <p className="font-medium">{test.worstStrategy}</p>
                    <p className="text-red-600">{formatPercentage(test.worstImpact)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Confidence</p>
                    <p className="font-medium">{formatPercentage(test.confidence * 100)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderAllocationTab = () => (
    <div className="space-y-6">
      {/* Allocation Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <PieChart className="h-5 w-5" />
            <span>Current Allocation</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
            <div className="text-center">
              <PieChart className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">Strategy Allocation Pie Chart</p>
              <p className="text-sm text-gray-500 mt-2">
                {allocationData.length} active strategies
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Strategy Details Table */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Strategy</th>
                  <th className="text-right py-2">Allocation</th>
                  <th className="text-right py-2">Value</th>
                  <th className="text-right py-2">1D Return</th>
                  <th className="text-right py-2">1M Return</th>
                  <th className="text-right py-2">Sharpe</th>
                  <th className="text-right py-2">Risk Contrib</th>
                </tr>
              </thead>
              <tbody>
                {allocationData.map(strategy => (
                  <tr key={strategy.strategy_id} className="border-b hover:bg-gray-50">
                    <td className="py-3">
                      <div>
                        <p className="font-medium">{strategy.strategy_name}</p>
                        <p className="text-xs text-gray-500">{strategy.strategy_id.slice(0, 8)}</p>
                      </div>
                    </td>
                    <td className="text-right py-3 font-medium">
                      {formatPercentage(strategy.allocation)}
                    </td>
                    <td className="text-right py-3">
                      {formatCurrency(strategy.value)}
                    </td>
                    <td className={`text-right py-3 ${getChangeColor(strategy.return_1d)}`}>
                      {formatPercentage(strategy.return_1d)}
                    </td>
                    <td className={`text-right py-3 ${getChangeColor(strategy.return_1m)}`}>
                      {formatPercentage(strategy.return_1m)}
                    </td>
                    <td className="text-right py-3">
                      {formatNumber(strategy.sharpe_ratio)}
                    </td>
                    <td className="text-right py-3">
                      {formatPercentage(strategy.risk_contribution)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Rebalancing History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Recent Rebalancing</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { date: '2024-01-15', action: 'Increased Growth Strategy allocation', change: '+2.5%' },
              { date: '2024-01-10', action: 'Reduced Bond Strategy exposure', change: '-1.8%' },
              { date: '2024-01-05', action: 'Added new Momentum Strategy', change: '+5.0%' }
            ].map((rebalance, index) => (
              <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="text-sm font-medium">{rebalance.action}</p>
                  <p className="text-xs text-gray-500">{rebalance.date}</p>
                </div>
                <Badge className={rebalance.change.startsWith('+') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                  {rebalance.change}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderAttributionTab = () => (
    <div className="space-y-6">
      {/* Attribution Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Performance Attribution</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Asset Allocation</p>
              <p className={`text-2xl font-bold ${getChangeColor(2.3)}`}>
                {formatPercentage(2.3)}
              </p>
              <p className="text-xs text-gray-500">Strategy selection</p>
            </div>
            
            <div className="text-center">
              <p className="text-sm text-gray-600">Security Selection</p>
              <p className={`text-2xl font-bold ${getChangeColor(1.7)}`}>
                {formatPercentage(1.7)}
              </p>
              <p className="text-xs text-gray-500">Stock picking</p>
            </div>
            
            <div className="text-center">
              <p className="text-sm text-gray-600">Timing Effect</p>
              <p className={`text-2xl font-bold ${getChangeColor(0.5)}`}>
                {formatPercentage(0.5)}
              </p>
              <p className="text-xs text-gray-500">Entry/exit timing</p>
            </div>
            
            <div className="text-center">
              <p className="text-sm text-gray-600">Interaction</p>
              <p className={`text-2xl font-bold ${getChangeColor(-0.2)}`}>
                {formatPercentage(-0.2)}
              </p>
              <p className="text-xs text-gray-500">Combined effects</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Strategy Contributions */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Contributions to Return</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {allocationData.map(strategy => (
              <div key={strategy.strategy_id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">{strategy.strategy_name}</h4>
                  <div className="text-right">
                    <p className={`font-medium ${getChangeColor(strategy.return_1m * strategy.allocation / 100)}`}>
                      {formatPercentage(strategy.return_1m * strategy.allocation / 100)}
                    </p>
                    <p className="text-xs text-gray-500">contribution</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Allocation</p>
                    <p className="font-medium">{formatPercentage(strategy.allocation)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Strategy Return</p>
                    <p className={`font-medium ${getChangeColor(strategy.return_1m)}`}>
                      {formatPercentage(strategy.return_1m)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Correlation</p>
                    <p className="font-medium">{formatNumber(strategy.correlation)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Factor Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Target className="h-5 w-5" />
            <span>Factor Exposure</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-3">Style Factors</h4>
              <div className="space-y-3">
                {[
                  { factor: 'Value', exposure: 0.15 },
                  { factor: 'Growth', exposure: 0.32 },
                  { factor: 'Quality', exposure: 0.28 },
                  { factor: 'Momentum', exposure: 0.42 }
                ].map(item => (
                  <div key={item.factor}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">{item.factor}</span>
                      <span className="text-sm font-medium">{formatNumber(item.exposure)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${Math.abs(item.exposure) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium mb-3">Risk Factors</h4>
              <div className="space-y-3">
                {[
                  { factor: 'Market Beta', exposure: 0.85 },
                  { factor: 'Interest Rate', exposure: -0.12 },
                  { factor: 'Credit Spread', exposure: 0.08 },
                  { factor: 'Volatility', exposure: -0.25 }
                ].map(item => (
                  <div key={item.factor}>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm">{item.factor}</span>
                      <span className={`text-sm font-medium ${getChangeColor(item.exposure)}`}>
                        {formatNumber(item.exposure)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${item.exposure >= 0 ? 'bg-green-500' : 'bg-red-500'}`}
                        style={{ width: `${Math.abs(item.exposure) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading portfolio analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Portfolio Analytics</h1>
          <p className="text-gray-600 mt-1">
            Comprehensive portfolio performance and risk analysis
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <Button
            onClick={() => setAutoRefresh(!autoRefresh)}
            variant="outline"
            size="sm"
            className="flex items-center space-x-2"
          >
            {autoRefresh ? <Activity className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
            <span>{autoRefresh ? 'Live' : 'Paused'}</span>
          </Button>

          <Button
            onClick={updateAnalyticsData}
            variant="outline"
            size="sm"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="flex items-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>Export</span>
          </Button>
        </div>
      </div>

      {/* Main Analytics Tabs */}
      <Tabs value={selectedTab} onValueChange={(value: any) => setSelectedTab(value)}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="risk">Risk</TabsTrigger>
          <TabsTrigger value="allocation">Allocation</TabsTrigger>
          <TabsTrigger value="attribution">Attribution</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">{renderOverviewTab()}</TabsContent>
        <TabsContent value="performance">{renderPerformanceTab()}</TabsContent>
        <TabsContent value="risk">{renderRiskTab()}</TabsContent>
        <TabsContent value="allocation">{renderAllocationTab()}</TabsContent>
        <TabsContent value="attribution">{renderAttributionTab()}</TabsContent>
      </Tabs>
    </div>
  );
}
