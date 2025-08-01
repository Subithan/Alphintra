import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Button } from '@/components/ui/no-code/button';
import { 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  Cpu, 
  Memory, 
  Zap,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Play,
  Pause,
  Square
} from 'lucide-react';
import { ExecutionResult, SignalResult } from '@/lib/execution-engine';
import { GeneratedCode } from '@/lib/advanced-code-generator';

interface PerformanceAnalyticsProps {
  executionResults: ExecutionResult[];
  generatedStrategy?: GeneratedCode;
  isExecuting: boolean;
  onStartExecution: () => void;
  onStopExecution: () => void;
  onClearHistory: () => void;
}

interface PerformanceMetrics {
  totalExecutions: number;
  totalSignals: number;
  avgExecutionTime: number;
  totalExecutionTime: number;
  avgMemoryUsage: number;
  maxMemoryUsage: number;
  errorRate: number;
  signalBreakdown: {
    buy: number;
    sell: number;
    hold: number;
  };
  recentPerformance: {
    last10Executions: number[];
    trend: 'improving' | 'stable' | 'degrading';
  };
}

export function PerformanceAnalytics({
  executionResults,
  generatedStrategy,
  isExecuting,
  onStartExecution,
  onStopExecution,
  onClearHistory
}: PerformanceAnalyticsProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1h' | '6h' | '24h' | 'all'>('1h');

  useEffect(() => {
    if (executionResults.length > 0) {
      const calculatedMetrics = calculateMetrics(executionResults, selectedTimeRange);
      setMetrics(calculatedMetrics);
    }
  }, [executionResults, selectedTimeRange]);

  const calculateMetrics = (results: ExecutionResult[], timeRange: string): PerformanceMetrics => {
    // Filter results based on time range
    const now = new Date();
    const timeRangeMs = timeRange === '1h' ? 3600000 : 
                       timeRange === '6h' ? 21600000 : 
                       timeRange === '24h' ? 86400000 : 
                       Number.MAX_SAFE_INTEGER;
    
    const filteredResults = timeRange === 'all' ? results : 
      results.filter(result => now.getTime() - result.timestamp.getTime() <= timeRangeMs);

    if (filteredResults.length === 0) {
      return {
        totalExecutions: 0,
        totalSignals: 0,
        avgExecutionTime: 0,
        totalExecutionTime: 0,
        avgMemoryUsage: 0,
        maxMemoryUsage: 0,
        errorRate: 0,
        signalBreakdown: { buy: 0, sell: 0, hold: 0 },
        recentPerformance: { last10Executions: [], trend: 'stable' }
      };
    }

    const totalExecutions = filteredResults.length;
    const allSignals = filteredResults.flatMap(result => result.signals);
    const totalSignals = allSignals.length;
    
    const executionTimes = filteredResults.map(result => result.performance_metrics.execution_time_ms);
    const avgExecutionTime = executionTimes.reduce((sum, time) => sum + time, 0) / executionTimes.length;
    const totalExecutionTime = executionTimes.reduce((sum, time) => sum + time, 0);
    
    const memoryUsages = filteredResults.map(result => result.performance_metrics.memory_usage_mb);
    const avgMemoryUsage = memoryUsages.reduce((sum, usage) => sum + usage, 0) / memoryUsages.length;
    const maxMemoryUsage = Math.max(...memoryUsages);
    
    const errorsCount = filteredResults.filter(result => result.errors.length > 0).length;
    const errorRate = (errorsCount / totalExecutions) * 100;
    
    const signalBreakdown = allSignals.reduce(
      (acc, signal) => {
        acc[signal.action]++;
        return acc;
      },
      { buy: 0, sell: 0, hold: 0 }
    );

    // Calculate recent performance trend
    const last10Executions = executionTimes.slice(-10);
    const trend = calculateTrend(last10Executions);

    return {
      totalExecutions,
      totalSignals,
      avgExecutionTime: Math.round(avgExecutionTime * 100) / 100,
      totalExecutionTime: Math.round(totalExecutionTime),
      avgMemoryUsage: Math.round(avgMemoryUsage * 100) / 100,
      maxMemoryUsage: Math.round(maxMemoryUsage * 100) / 100,
      errorRate: Math.round(errorRate * 100) / 100,
      signalBreakdown,
      recentPerformance: {
        last10Executions,
        trend
      }
    };
  };

  const calculateTrend = (executionTimes: number[]): 'improving' | 'stable' | 'degrading' => {
    if (executionTimes.length < 5) return 'stable';
    
    const firstHalf = executionTimes.slice(0, Math.floor(executionTimes.length / 2));
    const secondHalf = executionTimes.slice(Math.floor(executionTimes.length / 2));
    
    const firstHalfAvg = firstHalf.reduce((sum, time) => sum + time, 0) / firstHalf.length;
    const secondHalfAvg = secondHalf.reduce((sum, time) => sum + time, 0) / secondHalf.length;
    
    const improvement = ((firstHalfAvg - secondHalfAvg) / firstHalfAvg) * 100;
    
    if (improvement > 10) return 'improving';
    if (improvement < -10) return 'degrading';
    return 'stable';
  };

  const getStatusIcon = () => {
    if (isExecuting) {
      return <Activity className="h-4 w-4 text-green-500 animate-pulse" />;
    }
    return <Square className="h-4 w-4 text-gray-500" />;
  };

  const getStatusColor = () => {
    if (isExecuting) return 'bg-green-100 text-green-800 border-green-300';
    return 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'degrading':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <BarChart3 className="h-4 w-4 text-blue-500" />;
    }
  };

  if (!metrics && executionResults.length === 0) {
    return (
      <div className="space-y-6">
        {/* Execution Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Strategy Execution</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-4">
              <Badge className={getStatusColor()}>
                {getStatusIcon()}
                <span className="ml-2">{isExecuting ? 'Running' : 'Stopped'}</span>
              </Badge>
              
              <div className="flex space-x-2">
                {!isExecuting ? (
                  <Button onClick={onStartExecution} size="sm" className="flex items-center space-x-2">
                    <Play className="h-4 w-4" />
                    <span>Start</span>
                  </Button>
                ) : (
                  <Button onClick={onStopExecution} size="sm" variant="destructive" className="flex items-center space-x-2">
                    <Pause className="h-4 w-4" />
                    <span>Stop</span>
                  </Button>
                )}
              </div>
            </div>
            
            <div className="mt-4 text-center text-gray-500">
              <BarChart3 className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No execution data available</p>
              <p className="text-sm">Start the strategy to see performance metrics</p>
            </div>
          </CardContent>
        </Card>

        {/* Strategy Information */}
        {generatedStrategy && (
          <Card>
            <CardHeader>
              <CardTitle>Generated Strategy Info</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {generatedStrategy.complexity_score}
                  </div>
                  <div className="text-sm text-gray-600">Complexity Score</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {generatedStrategy.estimated_performance.execution_time_ms}ms
                  </div>
                  <div className="text-sm text-gray-600">Est. Execution</div>
                </div>
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {generatedStrategy.estimated_performance.memory_usage_mb}MB
                  </div>
                  <div className="text-sm text-gray-600">Est. Memory</div>
                </div>
                
                <div className="text-center">
                  <Badge 
                    className={
                      generatedStrategy.estimated_performance.cpu_intensity === 'high' ? 'bg-red-100 text-red-800' :
                      generatedStrategy.estimated_performance.cpu_intensity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }
                  >
                    {generatedStrategy.estimated_performance.cpu_intensity.toUpperCase()} CPU
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Execution Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Strategy Execution</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <select
                value={selectedTimeRange}
                onChange={(e) => setSelectedTimeRange(e.target.value as any)}
                className="text-sm border rounded px-2 py-1"
              >
                <option value="1h">Last Hour</option>
                <option value="6h">Last 6 Hours</option>
                <option value="24h">Last 24 Hours</option>
                <option value="all">All Time</option>
              </select>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Badge className={getStatusColor()}>
                {getStatusIcon()}
                <span className="ml-2">{isExecuting ? 'Running' : 'Stopped'}</span>
              </Badge>
              
              <div className="text-sm text-gray-600">
                {metrics?.totalExecutions || 0} executions • {metrics?.totalSignals || 0} signals
              </div>
            </div>
            
            <div className="flex space-x-2">
              {!isExecuting ? (
                <Button onClick={onStartExecution} size="sm" className="flex items-center space-x-2">
                  <Play className="h-4 w-4" />
                  <span>Start</span>
                </Button>
              ) : (
                <Button onClick={onStopExecution} size="sm" variant="destructive" className="flex items-center space-x-2">
                  <Pause className="h-4 w-4" />
                  <span>Stop</span>
                </Button>
              )}
              
              <Button onClick={onClearHistory} size="sm" variant="outline">
                Clear History
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      {metrics && (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-blue-500" />
                  <div>
                    <div className="text-2xl font-bold">{metrics.avgExecutionTime}ms</div>
                    <div className="text-sm text-gray-600">Avg Execution Time</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Memory className="h-4 w-4 text-purple-500" />
                  <div>
                    <div className="text-2xl font-bold">{metrics.avgMemoryUsage}MB</div>
                    <div className="text-sm text-gray-600">Avg Memory Usage</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Zap className="h-4 w-4 text-yellow-500" />
                  <div>
                    <div className="text-2xl font-bold">{metrics.totalSignals}</div>
                    <div className="text-sm text-gray-600">Total Signals</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  {metrics.errorRate > 0 ? (
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                  ) : (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  )}
                  <div>
                    <div className="text-2xl font-bold">{metrics.errorRate}%</div>
                    <div className="text-sm text-gray-600">Error Rate</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Signal Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Signal Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">{metrics.signalBreakdown.buy}</div>
                  <div className="text-sm text-gray-600">Buy Signals</div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600">{metrics.signalBreakdown.sell}</div>
                  <div className="text-sm text-gray-600">Sell Signals</div>
                </div>
                
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-600">{metrics.signalBreakdown.hold}</div>
                  <div className="text-sm text-gray-600">Hold Signals</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Performance Trend */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                {getTrendIcon(metrics.recentPerformance.trend)}
                <span>Performance Trend</span>
                <Badge 
                  className={
                    metrics.recentPerformance.trend === 'improving' ? 'bg-green-100 text-green-800' :
                    metrics.recentPerformance.trend === 'degrading' ? 'bg-red-100 text-red-800' :
                    'bg-blue-100 text-blue-800'
                  }
                >
                  {metrics.recentPerformance.trend}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Total Execution Time</div>
                    <div className="text-xl font-semibold">{metrics.totalExecutionTime}ms</div>
                  </div>
                  
                  <div>
                    <div className="text-sm text-gray-600 mb-1">Peak Memory Usage</div>
                    <div className="text-xl font-semibold">{metrics.maxMemoryUsage}MB</div>
                  </div>
                </div>
                
                {metrics.recentPerformance.last10Executions.length > 0 && (
                  <div>
                    <div className="text-sm text-gray-600 mb-2">Recent Execution Times (ms)</div>
                    <div className="flex space-x-1">
                      {metrics.recentPerformance.last10Executions.map((time, index) => (
                        <div
                          key={index}
                          className="flex-1 bg-blue-200 rounded"
                          style={{ 
                            height: `${Math.max((time / Math.max(...metrics.recentPerformance.last10Executions)) * 40, 4)}px` 
                          }}
                          title={`${time}ms`}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Recent Execution Results */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Executions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {executionResults.slice(-10).reverse().map((result, index) => (
                  <div key={result.execution_id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center space-x-3">
                      <div className="text-sm font-medium">
                        {result.timestamp.toLocaleTimeString()}
                      </div>
                      
                      <Badge variant="outline" className="text-xs">
                        {result.signals.length} signals
                      </Badge>
                      
                      {result.errors.length > 0 && (
                        <Badge className="bg-red-100 text-red-800 text-xs">
                          {result.errors.length} errors
                        </Badge>
                      )}
                      
                      {result.warnings.length > 0 && (
                        <Badge className="bg-yellow-100 text-yellow-800 text-xs">
                          {result.warnings.length} warnings
                        </Badge>
                      )}
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      {result.performance_metrics.execution_time_ms}ms
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}