import React, { useState, useEffect, useRef } from 'react';
import { Node, Edge } from 'reactflow';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Button } from '@/components/ui/no-code/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/no-code/tabs';
import { 
  Play, 
  Pause, 
  Square, 
  Settings, 
  TrendingUp, 
  TrendingDown,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Target,
  BarChart3,
  PieChart,
  LineChart,
  Brain,
  Shield,
  Database,
  Cpu,
  Server,
  Wifi,
  WifiOff,
  RefreshCw,
  Eye,
  EyeOff,
  Edit,
  Trash2,
  Plus,
  Download,
  Upload
} from 'lucide-react';
import { 
  StrategyOrchestrationEngine,
  StrategyInstance,
  OrchestrationState,
  OrchestrationAlert
} from '@/lib/strategy-orchestration-engine';
import { DebugPanel } from './DebugPanel';
import { PerformanceAnalytics } from './PerformanceAnalytics';

interface AdvancedStrategyDashboardProps {
  orchestrationEngine: StrategyOrchestrationEngine;
  onStrategyEdit: (strategyId: string) => void;
  onStrategyCreate: () => void;
}

interface StrategyCard {
  instance: StrategyInstance;
  isExpanded: boolean;
  showDebug: boolean;
  showPerformance: boolean;
}

export function AdvancedStrategyDashboard({
  orchestrationEngine,
  onStrategyEdit,
  onStrategyCreate
}: AdvancedStrategyDashboardProps) {
  const [orchestrationState, setOrchestrationState] = useState<OrchestrationState | null>(null);
  const [strategies, setStrategies] = useState<StrategyInstance[]>([]);
  const [strategyCards, setStrategyCards] = useState<Map<string, StrategyCard>>(new Map());
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'strategies' | 'performance' | 'risk' | 'system'>('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(1000);
  const refreshTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    updateDashboardData();
    
    if (autoRefresh) {
      refreshTimer.current = setInterval(() => {
        updateDashboardData();
      }, refreshInterval);
    }

    return () => {
      if (refreshTimer.current) {
        clearInterval(refreshTimer.current);
      }
    };
  }, [autoRefresh, refreshInterval]);

  const updateDashboardData = () => {
    try {
      const state = orchestrationEngine.getState();
      const strategyList = orchestrationEngine.getStrategies();
      
      setOrchestrationState(state);
      setStrategies(strategyList);

      // Initialize strategy cards if needed
      strategyList.forEach(strategy => {
        if (!strategyCards.has(strategy.instance_id)) {
          setStrategyCards(prev => new Map(prev.set(strategy.instance_id, {
            instance: strategy,
            isExpanded: false,
            showDebug: false,
            showPerformance: false
          })));
        }
      });
    } catch (error) {
      console.error('Error updating dashboard data:', error);
    }
  };

  const handleStrategyAction = async (strategyId: string, action: 'start' | 'pause' | 'stop' | 'remove') => {
    try {
      switch (action) {
        case 'start':
          await orchestrationEngine.resumeStrategy(strategyId);
          break;
        case 'pause':
          await orchestrationEngine.pauseStrategy(strategyId);
          break;
        case 'stop':
          await orchestrationEngine.pauseStrategy(strategyId);
          break;
        case 'remove':
          if (confirm('Are you sure you want to remove this strategy?')) {
            await orchestrationEngine.removeStrategy(strategyId);
          }
          break;
      }
      updateDashboardData();
    } catch (error) {
      console.error(`Error performing ${action} on strategy ${strategyId}:`, error);
    }
  };

  const handleSystemAction = async (action: 'start' | 'stop') => {
    try {
      if (action === 'start') {
        await orchestrationEngine.start();
      } else {
        await orchestrationEngine.stop();
      }
      updateDashboardData();
    } catch (error) {
      console.error(`Error performing system ${action}:`, error);
    }
  };

  const toggleStrategyExpansion = (strategyId: string) => {
    setStrategyCards(prev => {
      const newMap = new Map(prev);
      const card = newMap.get(strategyId);
      if (card) {
        newMap.set(strategyId, { ...card, isExpanded: !card.isExpanded });
      }
      return newMap;
    });
  };

  const toggleStrategyDebug = (strategyId: string) => {
    setStrategyCards(prev => {
      const newMap = new Map(prev);
      const card = newMap.get(strategyId);
      if (card) {
        newMap.set(strategyId, { ...card, showDebug: !card.showDebug });
      }
      return newMap;
    });
  };

  const toggleStrategyPerformance = (strategyId: string) => {
    setStrategyCards(prev => {
      const newMap = new Map(prev);
      const card = newMap.get(strategyId);
      if (card) {
        newMap.set(strategyId, { ...card, showPerformance: !card.showPerformance });
      }
      return newMap;
    });
  };

  const getStatusColor = (status: StrategyInstance['status']) => {
    switch (status) {
      case 'running': return 'bg-green-100 text-green-800 border-green-300';
      case 'paused': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'error': return 'bg-red-100 text-red-800 border-red-300';
      case 'optimizing': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'initializing': return 'bg-purple-100 text-purple-800 border-purple-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getSystemStatusColor = (status: OrchestrationState['status']) => {
    switch (status) {
      case 'running': return 'text-green-600';
      case 'starting': return 'text-blue-600';
      case 'pausing': return 'text-yellow-600';
      case 'stopped': return 'text-gray-600';
      case 'stopped_error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getHealthStatusIcon = (status: 'healthy' | 'warning' | 'critical') => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning': return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'critical': return <AlertTriangle className="h-5 w-5 text-red-500" />;
    }
  };

  const getConnectivityIcon = (status: 'connected' | 'degraded' | 'disconnected') => {
    switch (status) {
      case 'connected': return <Wifi className="h-4 w-4 text-green-500" />;
      case 'degraded': return <Wifi className="h-4 w-4 text-yellow-500" />;
      case 'disconnected': return <WifiOff className="h-4 w-4 text-red-500" />;
    }
  };

  const formatNumber = (num: number, decimals = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num);
  };

  const formatCurrency = (num: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(num);
  };

  const formatPercentage = (num: number) => {
    return `${num >= 0 ? '+' : ''}${formatNumber(num, 2)}%`;
  };

  if (!orchestrationState) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Strategy Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Advanced trading strategy orchestration and monitoring
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              orchestrationState.status === 'running' ? 'bg-green-500' : 
              orchestrationState.status === 'starting' ? 'bg-blue-500' :
              orchestrationState.status === 'stopped_error' ? 'bg-red-500' : 'bg-gray-500'
            }`} />
            <span className={`font-medium capitalize ${getSystemStatusColor(orchestrationState.status)}`}>
              {orchestrationState.status.replace('_', ' ')}
            </span>
          </div>

          <Button
            onClick={() => setAutoRefresh(!autoRefresh)}
            variant="outline"
            size="sm"
            className="flex items-center space-x-2"
          >
            {autoRefresh ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            <span>{autoRefresh ? 'Live' : 'Manual'}</span>
          </Button>

          {orchestrationState.status === 'stopped' ? (
            <Button
              onClick={() => handleSystemAction('start')}
              className="flex items-center space-x-2"
            >
              <Play className="h-4 w-4" />
              <span>Start System</span>
            </Button>
          ) : (
            <Button
              onClick={() => handleSystemAction('stop')}
              variant="destructive"
              className="flex items-center space-x-2"
            >
              <Square className="h-4 w-4" />
              <span>Stop System</span>
            </Button>
          )}
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Strategies</p>
                <p className="text-2xl font-bold">{orchestrationState.active_strategies}</p>
                <p className="text-xs text-gray-500">of {orchestrationState.total_strategies} total</p>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Portfolio Value</p>
                <p className="text-2xl font-bold">{formatCurrency(orchestrationState.performance_summary.portfolio_value)}</p>
                <p className={`text-xs ${orchestrationState.performance_summary.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercentage(orchestrationState.performance_summary.daily_pnl)}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">System Health</p>
                <p className="text-2xl font-bold capitalize">{orchestrationState.system_health.overall_status}</p>
                <p className="text-xs text-gray-500">
                  {formatNumber(orchestrationState.system_health.latency_ms)}ms latency
                </p>
              </div>
              {getHealthStatusIcon(orchestrationState.system_health.overall_status)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold">{formatNumber(orchestrationState.performance_summary.success_rate)}%</p>
                <p className="text-xs text-gray-500">
                  {orchestrationState.performance_summary.total_executions} executions
                </p>
              </div>
              <Target className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs value={activeTab} onValueChange={(value: any) => setActiveTab(value)}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="strategies">Strategies</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="risk">Risk</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Alerts */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <AlertTriangle className="h-5 w-5" />
                  <span>Recent Alerts</span>
                  <Badge className="ml-auto">{orchestrationState.alerts.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {orchestrationState.alerts.slice(-10).reverse().map(alert => (
                    <div
                      key={alert.alert_id}
                      className={`p-3 rounded border-l-4 ${
                        alert.severity === 'critical' ? 'border-red-500 bg-red-50' :
                        alert.severity === 'error' ? 'border-orange-500 bg-orange-50' :
                        alert.severity === 'warning' ? 'border-yellow-500 bg-yellow-50' :
                        'border-blue-500 bg-blue-50'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <Badge className={`text-xs ${
                              alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                              alert.severity === 'error' ? 'bg-orange-100 text-orange-800' :
                              alert.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-blue-100 text-blue-800'
                            }`}>
                              {alert.severity}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {alert.category}
                            </Badge>
                          </div>
                          <p className="mt-1 text-sm font-medium">{alert.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {alert.source} • {alert.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {orchestrationState.alerts.length === 0 && (
                    <div className="text-center py-4 text-gray-500">
                      <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
                      <p>No alerts</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* System Resource Usage */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Cpu className="h-5 w-5" />
                  <span>System Resources</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">CPU Usage</span>
                      <span className="text-sm text-gray-600">
                        {formatNumber(orchestrationState.system_health.cpu_usage)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          orchestrationState.system_health.cpu_usage > 80 ? 'bg-red-500' :
                          orchestrationState.system_health.cpu_usage > 60 ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                        style={{ width: `${orchestrationState.system_health.cpu_usage}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">Memory Usage</span>
                      <span className="text-sm text-gray-600">
                        {formatNumber(orchestrationState.system_health.memory_usage)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          orchestrationState.system_health.memory_usage > 80 ? 'bg-red-500' :
                          orchestrationState.system_health.memory_usage > 60 ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                        style={{ width: `${orchestrationState.system_health.memory_usage}%` }}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                    <div className="text-center">
                      <div className="flex items-center justify-center space-x-2">
                        {getConnectivityIcon(orchestrationState.system_health.data_connectivity)}
                        <span className="text-sm">Data</span>
                      </div>
                      <p className="text-xs text-gray-500 capitalize">
                        {orchestrationState.system_health.data_connectivity}
                      </p>
                    </div>
                    
                    <div className="text-center">
                      <div className="flex items-center justify-center space-x-2">
                        <Clock className="h-4 w-4 text-blue-500" />
                        <span className="text-sm">Uptime</span>
                      </div>
                      <p className="text-xs text-gray-500">
                        {Math.floor(orchestrationState.system_health.uptime_seconds / 3600)}h {Math.floor((orchestrationState.system_health.uptime_seconds % 3600) / 60)}m
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Strategies Tab */}
        <TabsContent value="strategies" className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Strategy Management</h2>
            <Button onClick={onStrategyCreate} className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>Add Strategy</span>
            </Button>
          </div>

          <div className="space-y-4">
            {strategies.map(strategy => {
              const card = strategyCards.get(strategy.instance_id);
              if (!card) return null;

              return (
                <Card key={strategy.instance_id} className="overflow-hidden">
                  <CardHeader 
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => toggleStrategyExpansion(strategy.instance_id)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div>
                          <CardTitle className="text-lg">{strategy.strategy_name}</CardTitle>
                          <p className="text-sm text-gray-600">{strategy.instance_id}</p>
                        </div>
                        
                        <Badge className={getStatusColor(strategy.status)}>
                          {strategy.status}
                        </Badge>
                        
                        {strategy.config.symbols.length > 0 && (
                          <div className="flex space-x-1">
                            {strategy.config.symbols.slice(0, 3).map(symbol => (
                              <Badge key={symbol} variant="outline" className="text-xs">
                                {symbol}
                              </Badge>
                            ))}
                            {strategy.config.symbols.length > 3 && (
                              <Badge variant="outline" className="text-xs">
                                +{strategy.config.symbols.length - 3}
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="flex items-center space-x-2">
                        <div className="text-right">
                          <p className="text-sm font-medium">
                            {formatCurrency(strategy.performance.total_pnl)}
                          </p>
                          <p className="text-xs text-gray-500">
                            {strategy.performance.signals_generated} signals
                          </p>
                        </div>

                        <div className="flex space-x-1">
                          {strategy.status === 'running' ? (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleStrategyAction(strategy.instance_id, 'pause');
                              }}
                            >
                              <Pause className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleStrategyAction(strategy.instance_id, 'start');
                              }}
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                          )}

                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              onStrategyEdit(strategy.instance_id);
                            }}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>

                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStrategyAction(strategy.instance_id, 'remove');
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardHeader>

                  {card.isExpanded && (
                    <CardContent className="border-t bg-gray-50">
                      <div className="space-y-4">
                        {/* Strategy Performance Metrics */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="text-center">
                            <p className="text-2xl font-bold text-green-600">
                              {formatNumber(strategy.performance.win_rate)}%
                            </p>
                            <p className="text-sm text-gray-600">Win Rate</p>
                          </div>
                          
                          <div className="text-center">
                            <p className="text-2xl font-bold text-blue-600">
                              {formatNumber(strategy.performance.sharpe_ratio)}
                            </p>
                            <p className="text-sm text-gray-600">Sharpe Ratio</p>
                          </div>
                          
                          <div className="text-center">
                            <p className="text-2xl font-bold text-purple-600">
                              {strategy.performance.total_executions}
                            </p>
                            <p className="text-sm text-gray-600">Executions</p>
                          </div>
                          
                          <div className="text-center">
                            <p className="text-2xl font-bold text-orange-600">
                              {formatNumber(strategy.performance.avg_execution_time_ms)}ms
                            </p>
                            <p className="text-sm text-gray-600">Avg Time</p>
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex items-center space-x-2 pt-4 border-t">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => toggleStrategyDebug(strategy.instance_id)}
                            className="flex items-center space-x-2"
                          >
                            <Activity className="h-4 w-4" />
                            <span>{card.showDebug ? 'Hide' : 'Show'} Debug</span>
                          </Button>

                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => toggleStrategyPerformance(strategy.instance_id)}
                            className="flex items-center space-x-2"
                          >
                            <BarChart3 className="h-4 w-4" />
                            <span>{card.showPerformance ? 'Hide' : 'Show'} Analytics</span>
                          </Button>

                          <Button
                            size="sm"
                            variant="outline"
                            className="flex items-center space-x-2"
                          >
                            <Brain className="h-4 w-4" />
                            <span>Optimize</span>
                          </Button>

                          <Button
                            size="sm"
                            variant="outline"
                            className="flex items-center space-x-2"
                          >
                            <Download className="h-4 w-4" />
                            <span>Export</span>
                          </Button>
                        </div>

                        {/* Debug Panel */}
                        {card.showDebug && (
                          <div className="mt-4">
                            <DebugPanel
                              nodes={strategy.nodes}
                              edges={strategy.edges}
                              executionResults={[]} // Would be populated with actual results
                              isDebugging={strategy.status === 'running'}
                              onStartDebugging={() => {}}
                              onStopDebugging={() => {}}
                              onStepDebugging={() => {}}
                              onResetDebugging={() => {}}
                            />
                          </div>
                        )}

                        {/* Performance Analytics */}
                        {card.showPerformance && (
                          <div className="mt-4">
                            <PerformanceAnalytics
                              executionResults={[]} // Would be populated with actual results
                              isExecuting={strategy.status === 'running'}
                              onStartExecution={() => {}}
                              onStopExecution={() => {}}
                              onClearHistory={() => {}}
                            />
                          </div>
                        )}
                      </div>
                    </CardContent>
                  )}
                </Card>
              );
            })}

            {strategies.length === 0 && (
              <Card>
                <CardContent className="text-center py-12">
                  <Plus className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium mb-2">No Strategies</h3>
                  <p className="text-gray-600 mb-4">
                    Get started by creating your first trading strategy
                  </p>
                  <Button onClick={onStrategyCreate} className="flex items-center space-x-2">
                    <Plus className="h-4 w-4" />
                    <span>Create Strategy</span>
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Portfolio Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Total P&L</p>
                      <p className={`text-2xl font-bold ${
                        orchestrationState.performance_summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {formatCurrency(orchestrationState.performance_summary.total_pnl)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Daily P&L</p>
                      <p className={`text-2xl font-bold ${
                        orchestrationState.performance_summary.daily_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {formatPercentage(orchestrationState.performance_summary.daily_pnl)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Sharpe Ratio</p>
                      <p className="text-xl font-bold">
                        {formatNumber(orchestrationState.performance_summary.portfolio_sharpe)}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Max Drawdown</p>
                      <p className="text-xl font-bold text-red-600">
                        {formatPercentage(orchestrationState.performance_summary.max_portfolio_drawdown)}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Execution Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Total Signals</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {orchestrationState.performance_summary.total_signals}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Executions</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {orchestrationState.performance_summary.total_executions}
                      </p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Success Rate</p>
                      <p className="text-xl font-bold text-green-600">
                        {formatNumber(orchestrationState.performance_summary.success_rate)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Avg Latency</p>
                      <p className="text-xl font-bold">
                        {formatNumber(orchestrationState.performance_summary.avg_latency_ms)}ms
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Risk Tab */}
        <TabsContent value="risk" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>Risk Management</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-gray-600 mb-2">Portfolio Risk</p>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-orange-600">Medium</p>
                    <p className="text-sm text-gray-500">Risk Level</p>
                  </div>
                </div>
                
                <div>
                  <p className="text-sm text-gray-600 mb-2">Position Count</p>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-blue-600">
                      {orchestrationState.performance_summary.active_positions}
                    </p>
                    <p className="text-sm text-gray-500">Active Positions</p>
                  </div>
                </div>
                
                <div>
                  <p className="text-sm text-gray-600 mb-2">Risk Alerts</p>
                  <div className="text-center">
                    <p className="text-3xl font-bold text-red-600">
                      {orchestrationState.alerts.filter(a => a.category === 'risk').length}
                    </p>
                    <p className="text-sm text-gray-500">Active Alerts</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Tab */}
        <TabsContent value="system" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="h-5 w-5" />
                  <span>System Status</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>Execution Engine</span>
                    <Badge className={
                      orchestrationState.system_health.execution_engine === 'operational' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }>
                      {orchestrationState.system_health.execution_engine}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span>Risk Management</span>
                    <Badge className={
                      orchestrationState.system_health.risk_management === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }>
                      {orchestrationState.system_health.risk_management}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span>Portfolio Manager</span>
                    <Badge className={
                      orchestrationState.system_health.portfolio_manager === 'operational' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }>
                      {orchestrationState.system_health.portfolio_manager}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span>Data Connectivity</span>
                    <div className="flex items-center space-x-2">
                      {getConnectivityIcon(orchestrationState.system_health.data_connectivity)}
                      <Badge className={
                        orchestrationState.system_health.data_connectivity === 'connected' 
                          ? 'bg-green-100 text-green-800' 
                          : orchestrationState.system_health.data_connectivity === 'degraded'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }>
                        {orchestrationState.system_health.data_connectivity}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Server className="h-5 w-5" />
                  <span>Resource Monitor</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-2">
                      <span>Memory</span>
                      <span>{formatNumber(orchestrationState.resource_usage.used_memory_mb)}MB / {formatNumber(orchestrationState.resource_usage.total_memory_mb)}MB</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ 
                          width: `${(orchestrationState.resource_usage.used_memory_mb / orchestrationState.resource_usage.total_memory_mb) * 100}%` 
                        }}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between mb-2">
                      <span>CPU Utilization</span>
                      <span>{formatNumber(orchestrationState.resource_usage.cpu_utilization)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${orchestrationState.resource_usage.cpu_utilization}%` }}
                      />
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Active Connections</p>
                        <p className="font-medium">{orchestrationState.resource_usage.active_connections}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Queue Size</p>
                        <p className="font-medium">{orchestrationState.resource_usage.execution_queue_size}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
