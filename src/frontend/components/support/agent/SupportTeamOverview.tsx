'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Users, 
  Clock, 
  MessageSquare, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle,
  RefreshCw,
  Activity,
  Star,
  Calendar,
  BarChart
} from 'lucide-react';
import { 
  customerSupportApi, 
  SupportAgent, 
  TicketStats,
  AgentStatus,
  AgentLevel,
  TicketStatus,
  TicketPriority
} from '@/lib/api/customer-support-api';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'react-hot-toast';

interface SupportTeamOverviewProps {
  currentAgentLevel: AgentLevel;
}

export default function SupportTeamOverview({ currentAgentLevel }: SupportTeamOverviewProps) {
  const [agents, setAgents] = useState<SupportAgent[]>([]);
  const [stats, setStats] = useState<TicketStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTeamData();
  }, []);

  const loadTeamData = async () => {
    setLoading(true);
    try {
      // Load all agents
      const agentsData = await customerSupportApi.getAgents();
      setAgents(agentsData);

      // Load overall stats
      const statsData = await customerSupportApi.getTicketStats();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load team data:', error);
      toast.error('Failed to load team data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: AgentStatus) => {
    switch (status) {
      case AgentStatus.AVAILABLE:
        return 'bg-green-500';
      case AgentStatus.BUSY:
        return 'bg-red-500';
      case AgentStatus.AWAY:
        return 'bg-yellow-500';
      case AgentStatus.BREAK:
        return 'bg-orange-500';
      case AgentStatus.OFFLINE:
        return 'bg-gray-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatAgentStatus = (status: AgentStatus) => {
    switch (status) {
      case AgentStatus.AVAILABLE:
        return 'Available';
      case AgentStatus.BUSY:
        return 'Busy';
      case AgentStatus.AWAY:
        return 'Away';
      case AgentStatus.BREAK:
        return 'On Break';
      case AgentStatus.OFFLINE:
        return 'Offline';
      default:
        return status;
    }
  };

  const getLevelColor = (level: AgentLevel) => {
    switch (level) {
      case AgentLevel.L1:
        return 'bg-blue-100 text-blue-800';
      case AgentLevel.L2:
        return 'bg-green-100 text-green-800';
      case AgentLevel.L3_SPECIALIST:
        return 'bg-purple-100 text-purple-800';
      case AgentLevel.L4_MANAGER:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getAgentsByLevel = (level: AgentLevel) => {
    return agents.filter(agent => agent.agentLevel === level);
  };

  const getAgentsByStatus = (status: AgentStatus) => {
    return agents.filter(agent => agent.status === status);
  };

  const getWorkloadColor = (current: number, max: number) => {
    const percentage = (current / max) * 100;
    if (percentage >= 90) return 'text-red-600';
    if (percentage >= 70) return 'text-orange-600';
    return 'text-green-600';
  };

  const calculateTeamMetrics = () => {
    const totalAgents = agents.length;
    const availableAgents = getAgentsByStatus(AgentStatus.AVAILABLE).length;
    const busyAgents = getAgentsByStatus(AgentStatus.BUSY).length;
    const totalCapacity = agents.reduce((sum, agent) => sum + agent.maxConcurrentTickets, 0);
    const currentLoad = agents.reduce((sum, agent) => sum + agent.currentTicketCount, 0);
    const avgSatisfaction = agents
      .filter(agent => agent.customerSatisfactionRating)
      .reduce((sum, agent) => sum + (agent.customerSatisfactionRating || 0), 0) / 
      agents.filter(agent => agent.customerSatisfactionRating).length;

    return {
      totalAgents,
      availableAgents,
      busyAgents,
      totalCapacity,
      currentLoad,
      capacityUtilization: (currentLoad / totalCapacity) * 100,
      avgSatisfaction: isNaN(avgSatisfaction) ? 0 : avgSatisfaction
    };
  };

  const metrics = calculateTeamMetrics();

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Support Team Overview</h2>
          <p className="text-gray-600">
            {metrics.totalAgents} total agents • {metrics.availableAgents} available • {metrics.busyAgents} busy
          </p>
        </div>
        <Button variant="outline" onClick={loadTeamData} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Team Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Agents</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.totalAgents}</p>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Capacity Used</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.capacityUtilization.toFixed(0)}%
                </p>
              </div>
              <Activity className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Tickets</p>
                <p className="text-2xl font-bold text-gray-900">{metrics.currentLoad}</p>
              </div>
              <MessageSquare className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Rating</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.avgSatisfaction > 0 ? metrics.avgSatisfaction.toFixed(1) : 'N/A'}
                </p>
              </div>
              <Star className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="agents" className="space-y-6">
        <TabsList>
          <TabsTrigger value="agents">All Agents</TabsTrigger>
          <TabsTrigger value="levels">By Level</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-6">
          {/* Agent Status Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Agent Status Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {Object.values(AgentStatus).map(status => {
                  const count = getAgentsByStatus(status).length;
                  return (
                    <div key={status} className="text-center">
                      <div className={`w-4 h-4 rounded-full mx-auto mb-2 ${getStatusColor(status)}`}></div>
                      <div className="text-2xl font-bold text-gray-900">{count}</div>
                      <div className="text-sm text-gray-600">{formatAgentStatus(status)}</div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* All Agents List */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                All Agents ({agents.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {agents.map(agent => (
                  <div key={agent.agentId} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`}></div>
                        <div>
                          <h3 className="font-medium text-gray-900">{agent.fullName}</h3>
                          <p className="text-sm text-gray-600">{agent.email}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Badge className={getLevelColor(agent.agentLevel)}>
                          {agent.agentLevel}
                        </Badge>
                        <Badge variant="outline">
                          {formatAgentStatus(agent.status)}
                        </Badge>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Workload:</span>
                        <div className={`font-medium ${getWorkloadColor(agent.currentTicketCount, agent.maxConcurrentTickets)}`}>
                          {agent.currentTicketCount}/{agent.maxConcurrentTickets}
                        </div>
                      </div>
                      
                      <div>
                        <span className="text-gray-500">Avg Resolution:</span>
                        <div className="font-medium">
                          {agent.averageResolutionTimeHours 
                            ? `${Math.round(agent.averageResolutionTimeHours)}h` 
                            : 'N/A'
                          }
                        </div>
                      </div>
                      
                      <div>
                        <span className="text-gray-500">Rating:</span>
                        <div className="flex items-center gap-1">
                          <Star className="w-3 h-3 text-yellow-400" />
                          <span className="font-medium">
                            {agent.customerSatisfactionRating 
                              ? agent.customerSatisfactionRating.toFixed(1)
                              : 'N/A'
                            }
                          </span>
                        </div>
                      </div>
                      
                      <div>
                        <span className="text-gray-500">Department:</span>
                        <div className="font-medium">{agent.department || 'General'}</div>
                      </div>
                    </div>

                    {agent.specializations && agent.specializations.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <span className="text-sm text-gray-500 mb-2 block">Specializations:</span>
                        <div className="flex flex-wrap gap-1">
                          {agent.specializations.map(spec => (
                            <Badge key={spec} variant="secondary" className="text-xs">
                              {spec.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="levels" className="space-y-6">
          {Object.values(AgentLevel).map(level => {
            const levelAgents = getAgentsByLevel(level);
            if (levelAgents.length === 0) return null;

            return (
              <Card key={level}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Badge className={getLevelColor(level)}>
                        {level.replace('_', ' ')}
                      </Badge>
                      <span>({levelAgents.length} agents)</span>
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {levelAgents.map(agent => (
                      <div key={agent.agentId} className="border rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`}></div>
                          <span className="font-medium text-sm">{agent.fullName}</span>
                        </div>
                        
                        <div className="text-xs text-gray-600 space-y-1">
                          <div className={getWorkloadColor(agent.currentTicketCount, agent.maxConcurrentTickets)}>
                            {agent.currentTicketCount}/{agent.maxConcurrentTickets} tickets
                          </div>
                          
                          {agent.customerSatisfactionRating && (
                            <div className="flex items-center gap-1">
                              <Star className="w-3 h-3 text-yellow-400" />
                              <span>{agent.customerSatisfactionRating.toFixed(1)}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          {/* Top Performers */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Top Performers
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {agents
                  .filter(agent => agent.customerSatisfactionRating && agent.customerSatisfactionRating > 0)
                  .sort((a, b) => (b.customerSatisfactionRating || 0) - (a.customerSatisfactionRating || 0))
                  .slice(0, 5)
                  .map((agent, index) => (
                    <div key={agent.agentId} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          index === 0 ? 'bg-yellow-500 text-white' :
                          index === 1 ? 'bg-gray-400 text-white' :
                          index === 2 ? 'bg-orange-600 text-white' :
                          'bg-gray-200 text-gray-600'
                        }`}>
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-medium">{agent.fullName}</div>
                          <div className="text-sm text-gray-600">{agent.agentLevel}</div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 text-yellow-400" />
                          <span className="font-medium">{agent.customerSatisfactionRating?.toFixed(1)}</span>
                        </div>
                        <div className="text-sm text-gray-600">
                          {agent.currentTicketCount} active tickets
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>

          {/* Performance Metrics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart className="w-5 h-5" />
                Performance Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h4 className="font-medium mb-3">Resolution Time Distribution</h4>
                  <div className="space-y-2">
                    {['< 1 hour', '1-4 hours', '4-8 hours', '8-24 hours', '> 24 hours'].map((range, index) => (
                      <div key={range} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">{range}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full" 
                              style={{ width: `${Math.random() * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium w-8">{Math.floor(Math.random() * 30)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}