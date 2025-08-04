import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/no-code/card';
import { Badge } from '@/components/ui/no-code/badge';
import { Button } from '@/components/ui/no-code/button';
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Cpu,
  Database,
  Eye,
  EyeOff,
  Maximize2,
  Minimize2,
  Pause,
  Play,
  RefreshCw,
  Settings,
  Shield,
  TrendingDown,
  TrendingUp,
  Wifi,
  WifiOff,
  Zap,
  BarChart3,
  LineChart,
  PieChart,
  Target,
  Bell,
  BellOff,
  Download,
  Filter,
  Search,
  Volume2,
  VolumeX
} from 'lucide-react';
import { 
  StrategyOrchestrationEngine,
  OrchestrationState,
  StrategyInstance,
  OrchestrationAlert
} from '@/lib/strategy-orchestration-engine';
import { 
  RealTimeDataEngine,
  ConnectionStatus,
  DataQualityMetrics,
  DataAlert
} from '@/lib/real-time-data-engine';

interface RealTimeControlCenterProps {
  orchestrationEngine: StrategyOrchestrationEngine;
  dataEngine: RealTimeDataEngine;
  onAlertClick: (alert: OrchestrationAlert | DataAlert) => void;
}

interface ControlPanelState {
  isFullscreen: boolean;
  autoRefresh: boolean;
  refreshInterval: number;
  soundEnabled: boolean;
  alertFilters: {
    severity: string[];
    category: string[];
  };
  viewMode: 'grid' | 'compact' | 'detailed';
}

interface MetricTile {
  id: string;
  title: string;
  value: string | number;
  change?: number;
  status: 'positive' | 'negative' | 'neutral' | 'warning';
  icon: React.ReactNode;
  trend?: number[];
  unit?: string;
  isExpanded?: boolean;
}

interface SystemMetrics {
  timestamp: Date;
  cpu_usage: number;
  memory_usage: number;
  network_throughput: number;
  active_connections: number;
  execution_latency: number;
  queue_size: number;
  error_rate: number;
  success_rate: number;
}

export function RealTimeControlCenter({
  orchestrationEngine,
  dataEngine,
  onAlertClick
}: RealTimeControlCenterProps) {
  const [orchestrationState, setOrchestrationState] = useState<OrchestrationState | null>(null);
  const [strategies, setStrategies] = useState<StrategyInstance[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus[]>([]);
  const [dataQuality, setDataQuality] = useState<DataQualityMetrics[]>([]);
  const [dataAlerts, setDataAlerts] = useState<DataAlert[]>([]);
  const [controlState, setControlState] = useState<ControlPanelState>({
    isFullscreen: false,
    autoRefresh: true,
    refreshInterval: 1000,
    soundEnabled: true,
    alertFilters: {
      severity: ['critical', 'error', 'warning'],
      category: ['system', 'strategy', 'risk', 'data']
    },
    viewMode: 'grid'
  });
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics[]>([]);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  const refreshTimer = useRef<NodeJS.Timeout | null>(null);
  const alertSound = useRef<HTMLAudioElement | null>(null);
  const previousAlertCount = useRef(0);

  useEffect(() => {
    // Initialize alert sound
    alertSound.current = new Audio('/alert-sound.mp3'); // You'd need to provide this audio file
    
    updateControlCenterData();
    
    if (controlState.autoRefresh) {
      refreshTimer.current = setInterval(() => {
        updateControlCenterData();
      }, controlState.refreshInterval);
    }

    return () => {
      if (refreshTimer.current) {
        clearInterval(refreshTimer.current);
      }
    };
  }, [controlState.autoRefresh, controlState.refreshInterval]);

  const updateControlCenterData = () => {
    try {
      // Get orchestration data
      const state = orchestrationEngine.getState();
      const strategyList = orchestrationEngine.getStrategies();
      
      setOrchestrationState(state);
      setStrategies(strategyList);

      // Get data engine status
      const connections = dataEngine.getConnectionStatus() as ConnectionStatus[];
      const quality = dataEngine.getQualityMetrics() as DataQualityMetrics[];
      const alerts = dataEngine.getAlerts();
      
      setConnectionStatus(Array.isArray(connections) ? connections : [connections]);
      setDataQuality(Array.isArray(quality) ? quality : [quality]);
      setDataAlerts(alerts);

      // Update system metrics
      const newMetrics: SystemMetrics = {
        timestamp: new Date(),
        cpu_usage: state.system_health.cpu_usage,
        memory_usage: state.system_health.memory_usage,
        network_throughput: state.resource_usage.data_throughput_mbps,
        active_connections: state.resource_usage.active_connections,
        execution_latency: state.system_health.latency_ms,
        queue_size: state.resource_usage.execution_queue_size,
        error_rate: 100 - state.performance_summary.success_rate,
        success_rate: state.performance_summary.success_rate
      };

      setSystemMetrics(prev => {
        const updated = [...prev, newMetrics];
        return updated.slice(-100); // Keep last 100 metrics
      });

      // Check for new alerts
      const currentAlertCount = state.alerts.length + alerts.length;
      if (currentAlertCount > previousAlertCount.current && controlState.soundEnabled) {
        playAlertSound();
      }
      previousAlertCount.current = currentAlertCount;

    } catch (error) {
      console.error('Error updating control center data:', error);
    }
  };

  const playAlertSound = () => {
    if (alertSound.current) {
      alertSound.current.play().catch(console.error);
    }
  };

  const toggleFullscreen = () => {
    setControlState(prev => ({ ...prev, isFullscreen: !prev.isFullscreen }));
  };

  const toggleAutoRefresh = () => {
    setControlState(prev => ({ ...prev, autoRefresh: !prev.autoRefresh }));
  };

  const toggleSound = () => {
    setControlState(prev => ({ ...prev, soundEnabled: !prev.soundEnabled }));
  };

  const handleRefreshIntervalChange = (interval: number) => {
    setControlState(prev => ({ ...prev, refreshInterval: interval }));
  };

  const handleViewModeChange = (mode: ControlPanelState['viewMode']) => {
    setControlState(prev => ({ ...prev, viewMode: mode }));
  };

  const getMetricTiles = (): MetricTile[] => {
    if (!orchestrationState) return [];

    return [
      {
        id: 'active_strategies',
        title: 'Active Strategies',
        value: orchestrationState.active_strategies,
        change: 0, // Would calculate change from previous value
        status: orchestrationState.active_strategies > 0 ? 'positive' : 'neutral',
        icon: <Activity className="h-5 w-5" />,
        trend: systemMetrics.slice(-10).map(m => m.success_rate)
      },
      {
        id: 'portfolio_value',
        title: 'Portfolio Value',
        value: orchestrationState.performance_summary.portfolio_value,
        change: orchestrationState.performance_summary.daily_pnl,
        status: orchestrationState.performance_summary.daily_pnl >= 0 ? 'positive' : 'negative',
        icon: <TrendingUp className="h-5 w-5" />,
        unit: '$',
        trend: systemMetrics.slice(-10).map((_, i) => 
          orchestrationState.performance_summary.portfolio_value + (Math.random() - 0.5) * 1000
        )
      },
      {
        id: 'system_health',
        title: 'System Health',
        value: orchestrationState.system_health.overall_status,
        status: orchestrationState.system_health.overall_status === 'healthy' ? 'positive' : 
                orchestrationState.system_health.overall_status === 'warning' ? 'warning' : 'negative',
        icon: <Shield className="h-5 w-5" />,
        trend: systemMetrics.slice(-10).map(m => m.cpu_usage)
      },
      {
        id: 'success_rate',
        title: 'Success Rate',
        value: orchestrationState.performance_summary.success_rate,
        change: 0,
        status: orchestrationState.performance_summary.success_rate > 90 ? 'positive' : 
                orchestrationState.performance_summary.success_rate > 70 ? 'warning' : 'negative',
        icon: <Target className="h-5 w-5" />,
        unit: '%',
        trend: systemMetrics.slice(-10).map(m => m.success_rate)
      },
      {
        id: 'cpu_usage',
        title: 'CPU Usage',
        value: orchestrationState.system_health.cpu_usage,
        status: orchestrationState.system_health.cpu_usage < 70 ? 'positive' : 
                orchestrationState.system_health.cpu_usage < 90 ? 'warning' : 'negative',
        icon: <Cpu className="h-5 w-5" />,
        unit: '%',
        trend: systemMetrics.slice(-10).map(m => m.cpu_usage)
      },
      {
        id: 'memory_usage',
        title: 'Memory Usage',
        value: orchestrationState.system_health.memory_usage,
        status: orchestrationState.system_health.memory_usage < 70 ? 'positive' : 
                orchestrationState.system_health.memory_usage < 90 ? 'warning' : 'negative',
        icon: <Database className="h-5 w-5" />,
        unit: '%',
        trend: systemMetrics.slice(-10).map(m => m.memory_usage)
      },
      {
        id: 'latency',
        title: 'Execution Latency',
        value: orchestrationState.system_health.latency_ms,
        status: orchestrationState.system_health.latency_ms < 100 ? 'positive' : 
                orchestrationState.system_health.latency_ms < 500 ? 'warning' : 'negative',
        icon: <Clock className="h-5 w-5" />,
        unit: 'ms',
        trend: systemMetrics.slice(-10).map(m => m.execution_latency)
      },
      {
        id: 'data_connectivity',
        title: 'Data Connectivity',
        value: connectionStatus.filter(c => c.status === 'connected').length,
        status: connectionStatus.every(c => c.status === 'connected') ? 'positive' : 
                connectionStatus.some(c => c.status === 'connected') ? 'warning' : 'negative',
        icon: connectionStatus.every(c => c.status === 'connected') ? 
              <Wifi className="h-5 w-5" /> : <WifiOff className="h-5 w-5" />,
        trend: systemMetrics.slice(-10).map(m => m.active_connections)
      }
    ];
  };

  const getStatusColor = (status: MetricTile['status']) => {
    switch (status) {
      case 'positive': return 'text-green-600 bg-green-50 border-green-200';
      case 'negative': return 'text-red-600 bg-red-50 border-red-200';
      case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'error': return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default: return <CheckCircle className="h-4 w-4 text-blue-500" />;
    }
  };

  const filteredAlerts = () => {
    const allAlerts = [
      ...(orchestrationState?.alerts || []).map(a => ({ ...a, source_type: 'orchestration' })),
      ...dataAlerts.map(a => ({ ...a, source_type: 'data' }))
    ];

    return allAlerts.filter(alert => {
      const severityMatch = controlState.alertFilters.severity.includes(alert.severity);
      const categoryMatch = controlState.alertFilters.category.includes(alert.category || alert.type);
      const searchMatch = searchTerm === '' || 
        alert.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (alert.provider || alert.source).toLowerCase().includes(searchTerm.toLowerCase());
      
      return severityMatch && categoryMatch && searchMatch;
    });
  };

  const renderMetricTile = (metric: MetricTile) => {
    const isSelected = selectedMetric === metric.id;
    
    return (
      <Card variant="glass" 
        key={metric.id}
        className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
          isSelected ? 'ring-2 ring-blue-500' : ''
        } ${getStatusColor(metric.status)}`}
        onClick={() => setSelectedMetric(isSelected ? null : metric.id)}
      >
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {metric.icon}
              <div>
                <p className="text-sm font-medium">{metric.title}</p>
                <div className="flex items-center space-x-2">
                  <p className="text-2xl font-bold">
                    {metric.unit === '$' 
                      ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(metric.value))
                      : typeof metric.value === 'number'
                      ? `${metric.value.toFixed(metric.unit === '%' ? 1 : 0)}${metric.unit || ''}`
                      : metric.value
                    }
                  </p>
                  {metric.change !== undefined && (
                    <span className={`text-sm ${metric.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {metric.change >= 0 ? '+' : ''}{metric.change.toFixed(2)}
                      {metric.unit === '$' ? '' : metric.unit || ''}
                    </span>
                  )}
                </div>
              </div>
            </div>
            
            {metric.trend && metric.trend.length > 0 && (
              <div className="w-16 h-8">
                <svg viewBox="0 0 64 32" className="w-full h-full">
                  <polyline
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    points={metric.trend.map((value, index) => {
                      const x = (index / (metric.trend!.length - 1)) * 64;
                      const y = 32 - ((value - Math.min(...metric.trend!)) / 
                        (Math.max(...metric.trend!) - Math.min(...metric.trend!))) * 32;
                      return `${x},${y}`;
                    }).join(' ')}
                  />
                </svg>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderAlertPanel = () => {
    const alerts = filteredAlerts();
    
    return (
      <Card variant="glass" className="col-span-full">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5" />
              <span>System Alerts</span>
              <Badge className="ml-2">{alerts.length}</Badge>
            </CardTitle>
            
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search alerts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <Button size="sm" variant="outline">
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="max-h-64 overflow-y-auto space-y-2">
            {alerts.slice(0, 20).map((alert, index) => (
              <div
                key={`${alert.alert_id || alert.source}-${index}`}
                onClick={() => onAlertClick(alert as any)}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
              >
                <div className="flex items-center space-x-3">
                  {getAlertIcon(alert.severity)}
                  <div>
                    <p className="text-sm font-medium">{alert.message}</p>
                    <div className="flex items-center space-x-2 text-xs text-gray-500">
                      <span>{alert.provider || alert.source}</span>
                      <span>•</span>
                      <span>{alert.timestamp.toLocaleTimeString()}</span>
                      {alert.symbol && (
                        <>
                          <span>•</span>
                          <span>{alert.symbol}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                
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
                    {alert.category || alert.type}
                  </Badge>
                </div>
              </div>
            ))}
            
            {alerts.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
                <p>No alerts matching current filters</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderConnectionStatus = () => {
    return (
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Wifi className="h-5 w-5" />
            <span>Data Connections</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {connectionStatus.map(connection => (
              <div key={connection.provider} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {connection.status === 'connected' ? 
                    <Wifi className="h-4 w-4 text-green-500" /> :
                    <WifiOff className="h-4 w-4 text-red-500" />
                  }
                  <div>
                    <p className="text-sm font-medium">{connection.provider}</p>
                    <p className="text-xs text-gray-500">
                      {connection.subscriptions_active} subscriptions • {connection.latency_ms}ms
                    </p>
                  </div>
                </div>
                <Badge className={
                  connection.status === 'connected' ? 'bg-green-100 text-green-800' :
                  connection.status === 'connecting' ? 'bg-blue-100 text-blue-800' :
                  'bg-red-100 text-red-800'
                }>
                  {connection.status}
                </Badge>
              </div>
            ))}
            
            {connectionStatus.length === 0 && (
              <div className="text-center py-4 text-gray-500">
                <WifiOff className="h-6 w-6 mx-auto mb-2" />
                <p className="text-sm">No data connections</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderControlPanel = () => {
    return (
      <Card variant="glass">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            <span>Control Panel</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Auto Refresh</span>
              <Button
                size="sm"
                variant="outline"
                onClick={toggleAutoRefresh}
                className="flex items-center space-x-2"
              >
                {controlState.autoRefresh ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                <span>{controlState.autoRefresh ? 'On' : 'Off'}</span>
              </Button>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Refresh Rate</span>
              <select
                value={controlState.refreshInterval}
                onChange={(e) => handleRefreshIntervalChange(Number(e.target.value))}
                className="px-3 py-1 border rounded text-sm"
              >
                <option value={500}>0.5s</option>
                <option value={1000}>1s</option>
                <option value={2000}>2s</option>
                <option value={5000}>5s</option>
              </select>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Sound Alerts</span>
              <Button
                size="sm"
                variant="outline"
                onClick={toggleSound}
                className="flex items-center space-x-2"
              >
                {controlState.soundEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                <span>{controlState.soundEnabled ? 'On' : 'Off'}</span>
              </Button>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">View Mode</span>
              <select
                value={controlState.viewMode}
                onChange={(e) => handleViewModeChange(e.target.value as ControlPanelState['viewMode'])}
                className="px-3 py-1 border rounded text-sm"
              >
                <option value="grid">Grid</option>
                <option value="compact">Compact</option>
                <option value="detailed">Detailed</option>
              </select>
            </div>
            
            <div className="pt-4 border-t">
              <Button
                size="sm"
                variant="outline"
                onClick={toggleFullscreen}
                className="w-full flex items-center justify-center space-x-2"
              >
                {controlState.isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                <span>{controlState.isFullscreen ? 'Exit' : 'Enter'} Fullscreen</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (!orchestrationState) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading control center...</p>
        </div>
      </div>
    );
  }

  const metricTiles = getMetricTiles();

  return (
    <div className={`space-y-6 ${controlState.isFullscreen ? 'fixed inset-0 z-50 bg-white p-6 overflow-auto' : ''}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Real-Time Control Center</h1>
          <p className="text-gray-600 mt-1">
            Live monitoring and control of trading operations
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full animate-pulse ${
              orchestrationState.status === 'running' ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm font-medium">Live Data</span>
          </div>
          
          <Button
            size="sm"
            variant="outline"
            onClick={updateControlCenterData}
            className="flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Metrics Grid */}
        <div className="lg:col-span-3">
          <div className={`grid gap-4 ${
            controlState.viewMode === 'grid' ? 'grid-cols-1 md:grid-cols-2 xl:grid-cols-4' :
            controlState.viewMode === 'compact' ? 'grid-cols-1 md:grid-cols-3 xl:grid-cols-6' :
            'grid-cols-1'
          }`}>
            {metricTiles.map(renderMetricTile)}
          </div>
          
          {/* Alerts Panel */}
          <div className="mt-6">
            {renderAlertPanel()}
          </div>
        </div>

        {/* Side Panel */}
        <div className="space-y-6">
          {renderConnectionStatus()}
          {renderControlPanel()}
          
          {/* Quick Actions */}
          <Card variant="glass">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Zap className="h-5 w-5" />
                <span>Quick Actions</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => {}}
                >
                  <Play className="h-4 w-4 mr-2" />
                  Start All Strategies
                </Button>
                
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => {}}
                >
                  <Pause className="h-4 w-4 mr-2" />
                  Pause All Strategies
                </Button>
                
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => {}}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export Logs
                </Button>
                
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => {}}
                >
                  <Bell className="h-4 w-4 mr-2" />
                  Test Alerts
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}