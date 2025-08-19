'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  BarChart, 
  LineChart, 
  TrendingUp, 
  TrendingDown,
  Users, 
  Clock, 
  MessageSquare, 
  Star,
  AlertTriangle,
  CheckCircle,
  Target,
  Activity,
  Download,
  RefreshCw,
  Calendar,
  Filter
} from 'lucide-react';
import { 
  customerSupportApi,
  TicketStats,
  TicketStatus,
  TicketPriority,
  TicketCategory
} from '@/lib/api/customer-support-api';
import { formatDistanceToNow, format, subDays, startOfDay, endOfDay } from 'date-fns';
import { toast } from 'react-hot-toast';

interface SupportAnalyticsDashboardProps {
  isManagerView?: boolean;
  agentId?: string;
  dateRange?: 'today' | '7days' | '30days' | '90days' | 'custom';
}

interface AnalyticsData {
  overview: {
    totalTickets: number;
    openTickets: number;
    resolvedTickets: number;
    avgResolutionTime: number;
    customerSatisfaction: number;
    firstResponseTime: number;
    slaCompliance: number;
  };
  trends: {
    ticketVolume: Array<{ date: string; count: number; }>;
    resolutionTimes: Array<{ date: string; time: number; }>;
    satisfactionScores: Array<{ date: string; score: number; }>;
  };
  breakdowns: {
    byCategory: Record<string, number>;
    byPriority: Record<string, number>;
    byStatus: Record<string, number>;
    byAgent: Array<{ agentId: string; agentName: string; tickets: number; avgResolution: number; satisfaction: number; }>;
  };
  performance: {
    slaMetrics: {
      firstResponse: { target: number; actual: number; compliance: number; };
      resolution: { target: number; actual: number; compliance: number; };
    };
    escalationRate: number;
    reopenRate: number;
    resolutionRate: number;
  };
}

// Mock analytics data
const mockAnalyticsData: AnalyticsData = {
  overview: {
    totalTickets: 1247,
    openTickets: 89,
    resolvedTickets: 1158,
    avgResolutionTime: 4.2,
    customerSatisfaction: 4.6,
    firstResponseTime: 0.8,
    slaCompliance: 94.2
  },
  trends: {
    ticketVolume: [
      { date: '2024-01-01', count: 45 },
      { date: '2024-01-02', count: 52 },
      { date: '2024-01-03', count: 38 },
      { date: '2024-01-04', count: 61 },
      { date: '2024-01-05', count: 44 },
      { date: '2024-01-06', count: 33 },
      { date: '2024-01-07', count: 48 }
    ],
    resolutionTimes: [
      { date: '2024-01-01', time: 4.5 },
      { date: '2024-01-02', time: 3.8 },
      { date: '2024-01-03', time: 4.1 },
      { date: '2024-01-04', time: 5.2 },
      { date: '2024-01-05', time: 3.9 },
      { date: '2024-01-06', time: 4.0 },
      { date: '2024-01-07', time: 4.3 }
    ],
    satisfactionScores: [
      { date: '2024-01-01', score: 4.5 },
      { date: '2024-01-02', score: 4.7 },
      { date: '2024-01-03', score: 4.6 },
      { date: '2024-01-04', score: 4.4 },
      { date: '2024-01-05', score: 4.8 },
      { date: '2024-01-06', score: 4.7 },
      { date: '2024-01-07', score: 4.6 }
    ]
  },
  breakdowns: {
    byCategory: {
      'Technical': 35,
      'Strategy Development': 28,
      'Live Trading': 22,
      'Account & Billing': 15
    },
    byPriority: {
      'Low': 45,
      'Medium': 30,
      'High': 20,
      'Urgent': 4,
      'Critical': 1
    },
    byStatus: {
      'New': 12,
      'Assigned': 25,
      'In Progress': 35,
      'Resolved': 28
    },
    byAgent: [
      { agentId: '1', agentName: 'Sarah Johnson', tickets: 127, avgResolution: 3.8, satisfaction: 4.8 },
      { agentId: '2', agentName: 'Mike Chen', tickets: 95, avgResolution: 4.2, satisfaction: 4.6 },
      { agentId: '3', agentName: 'Emma Wilson', tickets: 110, avgResolution: 3.9, satisfaction: 4.7 },
      { agentId: '4', agentName: 'David Rodriguez', tickets: 88, avgResolution: 4.5, satisfaction: 4.5 }
    ]
  },
  performance: {
    slaMetrics: {
      firstResponse: { target: 1.0, actual: 0.8, compliance: 95.2 },
      resolution: { target: 6.0, actual: 4.2, compliance: 94.2 }
    },
    escalationRate: 8.5,
    reopenRate: 3.2,
    resolutionRate: 92.8
  }
};

export default function SupportAnalyticsDashboard({ 
  isManagerView = false, 
  agentId,
  dateRange = '30days'
}: SupportAnalyticsDashboardProps) {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData>(mockAnalyticsData);
  const [loading, setLoading] = useState(false);
  const [selectedDateRange, setSelectedDateRange] = useState(dateRange);
  const [selectedMetric, setSelectedMetric] = useState<'volume' | 'resolution' | 'satisfaction'>('volume');
  const [customDateRange, setCustomDateRange] = useState<{ start: Date; end: Date } | null>(null);

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedDateRange, agentId]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      // In real implementation, this would fetch from the API
      // const data = await customerSupportApi.getAnalytics(selectedDateRange, agentId);
      // setAnalyticsData(data);
      
      // Simulate API delay
      setTimeout(() => {
        setAnalyticsData(mockAnalyticsData);
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
      toast.error('Failed to load analytics data');
      setLoading(false);
    }
  };

  const exportData = async (format: 'csv' | 'pdf') => {
    try {
      toast.success(`Exporting analytics data as ${format.toUpperCase()}...`);
      // In real implementation, this would call the export API
    } catch (error) {
      toast.error('Failed to export data');
    }
  };

  const MetricCard = ({ 
    title, 
    value, 
    change, 
    icon: Icon, 
    color = 'blue',
    format = 'number',
    target,
    unit = ''
  }: any) => {
    const formatValue = (val: number) => {
      switch (format) {
        case 'percentage':
          return `${val}%`;
        case 'hours':
          return `${val}h`;
        case 'rating':
          return `${val}/5`;
        case 'time':
          return `${val}h`;
        default:
          return val.toLocaleString();
      }
    };

    const getChangeColor = (change: number) => {
      if (change > 0) return 'text-green-600';
      if (change < 0) return 'text-red-600';
      return 'text-gray-600';
    };

    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <div className="flex items-baseline gap-2">
                <p className="text-2xl font-bold text-gray-900">
                  {formatValue(value)}{unit}
                </p>
                {change !== undefined && (
                  <span className={`text-sm font-medium ${getChangeColor(change)}`}>
                    {change > 0 ? '+' : ''}{change}%
                  </span>
                )}
              </div>
              {target && (
                <p className="text-xs text-gray-500 mt-1">
                  Target: {formatValue(target)}{unit}
                </p>
              )}
            </div>
            <Icon className={`w-8 h-8 text-${color}-500`} />
          </div>
        </CardContent>
      </Card>
    );
  };

  const SimpleChart = ({ data, type, title }: any) => {
    const maxValue = Math.max(...data.map((d: any) => d.count || d.time || d.score));
    
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.map((item: any, index: number) => {
              const value = item.count || item.time || item.score;
              const width = (value / maxValue) * 100;
              
              return (
                <div key={index} className="flex items-center gap-3">
                  <span className="text-xs text-gray-500 w-16">
                    {format(new Date(item.date), 'MMM d')}
                  </span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${width}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium w-12 text-right">
                    {type === 'rating' ? value.toFixed(1) : Math.round(value)}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    );
  };

  const CategoryBreakdown = ({ data, title }: any) => {
    const total = Object.values(data).reduce((sum: number, val: number) => sum + val, 0);
    
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(data).map(([category, count]: [string, any]) => {
              const percentage = ((count / total) * 100).toFixed(1);
              
              return (
                <div key={category} className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <span className="text-sm text-gray-700">{category}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{count}</span>
                    <span className="text-xs text-gray-500">({percentage}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    );
  };

  const AgentPerformanceTable = ({ agents }: any) => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Agent Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Agent</th>
                <th className="text-right py-2">Tickets</th>
                <th className="text-right py-2">Avg Resolution</th>
                <th className="text-right py-2">Satisfaction</th>
                <th className="text-right py-2">Performance</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent: any) => (
                <tr key={agent.agentId} className="border-b">
                  <td className="py-3">
                    <div>
                      <div className="font-medium">{agent.agentName}</div>
                      <div className="text-xs text-gray-500">ID: {agent.agentId}</div>
                    </div>
                  </td>
                  <td className="text-right py-3">{agent.tickets}</td>
                  <td className="text-right py-3">{agent.avgResolution}h</td>
                  <td className="text-right py-3">
                    <div className="flex items-center justify-end gap-1">
                      <Star className="w-3 h-3 text-yellow-400 fill-current" />
                      {agent.satisfaction.toFixed(1)}
                    </div>
                  </td>
                  <td className="text-right py-3">
                    <Badge 
                      variant={agent.satisfaction >= 4.5 ? 'default' : agent.satisfaction >= 4.0 ? 'secondary' : 'destructive'}
                      className="text-xs"
                    >
                      {agent.satisfaction >= 4.5 ? 'Excellent' : agent.satisfaction >= 4.0 ? 'Good' : 'Needs Improvement'}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-8 bg-gray-200 rounded w-1/2"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {isManagerView ? 'Support Analytics Dashboard' : 'My Performance Analytics'}
          </h1>
          <p className="text-gray-600">
            Comprehensive insights into support team performance and customer satisfaction
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={selectedDateRange} onValueChange={setSelectedDateRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="7days">7 Days</SelectItem>
              <SelectItem value="30days">30 Days</SelectItem>
              <SelectItem value="90days">90 Days</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" onClick={loadAnalyticsData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button variant="outline" onClick={() => exportData('csv')}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Tickets"
          value={analyticsData.overview.totalTickets}
          change={8.2}
          icon={MessageSquare}
          color="blue"
        />
        
        <MetricCard
          title="Avg Resolution Time"
          value={analyticsData.overview.avgResolutionTime}
          change={-12.3}
          icon={Clock}
          color="green"
          format="hours"
          target={6.0}
        />
        
        <MetricCard
          title="Customer Satisfaction"
          value={analyticsData.overview.customerSatisfaction}
          change={2.1}
          icon={Star}
          color="yellow"
          format="rating"
          target={4.5}
        />
        
        <MetricCard
          title="SLA Compliance"
          value={analyticsData.overview.slaCompliance}
          change={1.8}
          icon={Target}
          color="purple"
          format="percentage"
          target={95}
        />
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Open Tickets"
          value={analyticsData.overview.openTickets}
          change={-5.2}
          icon={AlertTriangle}
          color="orange"
        />
        
        <MetricCard
          title="Resolved Tickets"
          value={analyticsData.overview.resolvedTickets}
          change={9.1}
          icon={CheckCircle}
          color="green"
        />
        
        <MetricCard
          title="First Response Time"
          value={analyticsData.overview.firstResponseTime}
          change={-8.7}
          icon={Activity}
          color="blue"
          format="hours"
          target={1.0}
        />
        
        <MetricCard
          title="Resolution Rate"
          value={analyticsData.performance.resolutionRate}
          change={3.4}
          icon={TrendingUp}
          color="green"
          format="percentage"
          target={95}
        />
      </div>

      <Tabs defaultValue="trends" className="space-y-6">
        <TabsList>
          <TabsTrigger value="trends">Trends & Charts</TabsTrigger>
          <TabsTrigger value="breakdowns">Category Breakdowns</TabsTrigger>
          <TabsTrigger value="performance">Team Performance</TabsTrigger>
          <TabsTrigger value="sla">SLA & Goals</TabsTrigger>
        </TabsList>

        <TabsContent value="trends" className="space-y-6">
          {/* Trend Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <SimpleChart
              data={analyticsData.trends.ticketVolume}
              type="count"
              title="Ticket Volume Trend"
            />
            
            <SimpleChart
              data={analyticsData.trends.resolutionTimes}
              type="time"
              title="Resolution Time Trend"
            />
            
            <SimpleChart
              data={analyticsData.trends.satisfactionScores}
              type="rating"
              title="Satisfaction Trend"
            />
          </div>

          {/* Advanced Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Performance Indicators</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Escalation Rate</span>
                    <span className="font-medium">{analyticsData.performance.escalationRate}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Reopen Rate</span>
                    <span className="font-medium">{analyticsData.performance.reopenRate}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Resolution Rate</span>
                    <span className="font-medium">{analyticsData.performance.resolutionRate}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Response Times</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-600">First Response</span>
                      <span className="font-medium">{analyticsData.overview.firstResponseTime}h</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full"
                        style={{ width: `${(analyticsData.performance.slaMetrics.firstResponse.compliance)}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {analyticsData.performance.slaMetrics.firstResponse.compliance}% within SLA
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-600">Resolution</span>
                      <span className="font-medium">{analyticsData.overview.avgResolutionTime}h</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${(analyticsData.performance.slaMetrics.resolution.compliance)}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {analyticsData.performance.slaMetrics.resolution.compliance}% within SLA
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Workload Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Peak Hours</span>
                    <span className="font-medium">10-12 AM</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Avg Daily Volume</span>
                    <span className="font-medium">47 tickets</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Busiest Day</span>
                    <span className="font-medium">Tuesday</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="breakdowns" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <CategoryBreakdown
              data={analyticsData.breakdowns.byCategory}
              title="Tickets by Category"
            />
            
            <CategoryBreakdown
              data={analyticsData.breakdowns.byPriority}
              title="Tickets by Priority"
            />
            
            <CategoryBreakdown
              data={analyticsData.breakdowns.byStatus}
              title="Tickets by Status"
            />
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          {isManagerView && (
            <AgentPerformanceTable agents={analyticsData.breakdowns.byAgent} />
          )}
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Top Performing Agents</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analyticsData.breakdowns.byAgent
                    .sort((a, b) => b.satisfaction - a.satisfaction)
                    .slice(0, 5)
                    .map((agent, index) => (
                      <div key={agent.agentId} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                            index === 0 ? 'bg-yellow-500 text-white' :
                            index === 1 ? 'bg-gray-400 text-white' :
                            index === 2 ? 'bg-orange-600 text-white' :
                            'bg-gray-200 text-gray-600'
                          }`}>
                            {index + 1}
                          </div>
                          <span className="font-medium">{agent.agentName}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 text-yellow-400 fill-current" />
                          <span>{agent.satisfaction.toFixed(1)}</span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Resolution Efficiency</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analyticsData.breakdowns.byAgent
                    .sort((a, b) => a.avgResolution - b.avgResolution)
                    .slice(0, 5)
                    .map((agent, index) => (
                      <div key={agent.agentId} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                            index === 0 ? 'bg-green-500 text-white' :
                            index === 1 ? 'bg-blue-500 text-white' :
                            index === 2 ? 'bg-purple-500 text-white' :
                            'bg-gray-200 text-gray-600'
                          }`}>
                            {index + 1}
                          </div>
                          <span className="font-medium">{agent.agentName}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4 text-gray-400" />
                          <span>{agent.avgResolution}h</span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="sla" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">SLA Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">First Response SLA</span>
                      <span className="text-sm text-gray-600">
                        Target: {analyticsData.performance.slaMetrics.firstResponse.target}h
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-green-500 h-3 rounded-full flex items-center justify-end pr-2"
                        style={{ width: `${analyticsData.performance.slaMetrics.firstResponse.compliance}%` }}
                      >
                        <span className="text-xs text-white font-medium">
                          {analyticsData.performance.slaMetrics.firstResponse.compliance}%
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Actual: {analyticsData.performance.slaMetrics.firstResponse.actual}h average
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">Resolution SLA</span>
                      <span className="text-sm text-gray-600">
                        Target: {analyticsData.performance.slaMetrics.resolution.target}h
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-blue-500 h-3 rounded-full flex items-center justify-end pr-2"
                        style={{ width: `${analyticsData.performance.slaMetrics.resolution.compliance}%` }}
                      >
                        <span className="text-xs text-white font-medium">
                          {analyticsData.performance.slaMetrics.resolution.compliance}%
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Actual: {analyticsData.performance.slaMetrics.resolution.actual}h average
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Goal Tracking</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="font-medium text-green-800">Monthly Goals</span>
                    </div>
                    <div className="text-sm text-green-700">
                      <div>Customer Satisfaction: 4.6/5 ✓</div>
                      <div>Resolution Rate: 92.8% ✓</div>
                      <div>SLA Compliance: 94.2% ✓</div>
                    </div>
                  </div>

                  <div className="p-4 bg-yellow-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-5 h-5 text-yellow-600" />
                      <span className="font-medium text-yellow-800">Areas for Improvement</span>
                    </div>
                    <div className="text-sm text-yellow-700">
                      <div>Escalation Rate: 8.5% (Target: <5%)</div>
                      <div>Reopen Rate: 3.2% (Target: <2%)</div>
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