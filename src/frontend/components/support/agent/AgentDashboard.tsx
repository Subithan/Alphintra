'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Clock, 
  MessageSquare, 
  Users, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp,
  Star,
  RefreshCw,
  Filter,
  Calendar,
  User,
  Settings
} from 'lucide-react';
import { 
  customerSupportApi, 
  Ticket, 
  SupportAgent,
  TicketStats,
  TicketStatus,
  AgentStatus,
  TicketPriority,
  formatStatus,
  formatPriority,
  getStatusColor,
  getPriorityColor
} from '@/lib/api/customer-support-api';
import { formatDistanceToNow } from 'date-fns';
import TicketList from '../ticket/TicketList';
import TicketDetailModal from '../ticket/TicketDetailModal';
import { toast } from 'react-hot-toast';

interface AgentDashboardProps {
  agentId: string;
  agentName: string;
  agentLevel: string;
}

export default function AgentDashboard({ agentId, agentName, agentLevel }: AgentDashboardProps) {
  const [agent, setAgent] = useState<SupportAgent | null>(null);
  const [stats, setStats] = useState<TicketStats | null>(null);
  const [myTickets, setMyTickets] = useState<Ticket[]>([]);
  const [urgentTickets, setUrgentTickets] = useState<Ticket[]>([]);
  const [recentTickets, setRecentTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [statusFilter, setStatusFilter] = useState<TicketStatus[]>([
    TicketStatus.NEW, 
    TicketStatus.ASSIGNED, 
    TicketStatus.IN_PROGRESS
  ]);

  useEffect(() => {
    loadDashboardData();
  }, [agentId]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load agent details
      const agents = await customerSupportApi.getAgents();
      const currentAgent = agents.find(a => a.agentId === agentId);
      if (currentAgent) {
        setAgent(currentAgent);
      }

      // Load agent tickets
      const myTicketsResponse = await customerSupportApi.getTickets(
        { agentId, status: TicketStatus.ASSIGNED }, 0, 10
      );
      setMyTickets(myTicketsResponse.content);

      // Load urgent tickets (unassigned or assigned to me)
      const urgentResponse = await customerSupportApi.getTickets(
        { priority: TicketPriority.URGENT }, 0, 5
      );
      setUrgentTickets(urgentResponse.content);

      // Load recent tickets (all new tickets)
      const recentResponse = await customerSupportApi.getTickets(
        { status: TicketStatus.NEW }, 0, 10
      );
      setRecentTickets(recentResponse.content);

      // Load overall stats
      const statsResponse = await customerSupportApi.getTicketStats();
      setStats(statsResponse);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus: AgentStatus) => {
    if (!agent) return;
    
    try {
      const updatedAgent = await customerSupportApi.updateAgentStatus(agentId, newStatus);
      setAgent(updatedAgent);
      toast.success('Status updated successfully');
    } catch (error) {
      console.error('Failed to update status:', error);
      toast.error('Failed to update status');
    }
  };

  const handleTicketClick = (ticket: Ticket) => {
    setSelectedTicket(ticket);
  };

  const handleTicketUpdated = (updatedTicket: Ticket) => {
    // Update ticket in various lists
    setMyTickets(prev => prev.map(t => t.ticketId === updatedTicket.ticketId ? updatedTicket : t));
    setUrgentTickets(prev => prev.map(t => t.ticketId === updatedTicket.ticketId ? updatedTicket : t));
    setRecentTickets(prev => prev.map(t => t.ticketId === updatedTicket.ticketId ? updatedTicket : t));
    setSelectedTicket(updatedTicket);
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
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

  const QuickStatCard = ({ title, value, icon: Icon, color }: any) => (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
          </div>
          <Icon className={`w-8 h-8 ${color}`} />
        </div>
      </CardContent>
    </Card>
  );

  const TicketCard = ({ ticket, onClick }: { ticket: Ticket; onClick: () => void }) => (
    <div 
      className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4" />
          <span className="text-sm font-medium text-gray-600">
            #{ticket.ticketId}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Badge className={getStatusColor(ticket.status)}>
            {formatStatus(ticket.status)}
          </Badge>
          <Badge className={getPriorityColor(ticket.priority)}>
            {formatPriority(ticket.priority)}
          </Badge>
        </div>
      </div>
      
      <h3 className="font-medium text-gray-900 mb-1 truncate">
        {ticket.title}
      </h3>
      
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
        {ticket.description}
      </p>
      
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>
          {formatDistanceToNow(new Date(ticket.createdAt), { addSuffix: true })}
        </span>
        {ticket.hasUnreadMessages && (
          <span className="flex items-center gap-1 text-blue-600 font-medium">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            New
          </span>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {getGreeting()}, {agentName}
          </h1>
          <p className="text-gray-600 mt-1">
            Support Agent Dashboard - {agentLevel} Level
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Agent Status */}
          {agent && (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`}></div>
                <span className="text-sm font-medium">{formatAgentStatus(agent.status)}</span>
              </div>
              <Select
                value={agent.status}
                onValueChange={(value) => handleStatusChange(value as AgentStatus)}
              >
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.values(AgentStatus).map(status => (
                    <SelectItem key={status} value={status}>
                      {formatAgentStatus(status)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          
          <Button variant="outline" onClick={loadDashboardData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      {loading ? (
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
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <QuickStatCard
            title="My Open Tickets"
            value={agent?.currentTicketCount || 0}
            icon={MessageSquare}
            color="text-blue-500"
          />
          <QuickStatCard
            title="Urgent Tickets"
            value={urgentTickets.length}
            icon={AlertTriangle}
            color="text-red-500"
          />
          <QuickStatCard
            title="Today's Resolution"
            value={stats?.resolvedTickets || 0}
            icon={CheckCircle}
            color="text-green-500"
          />
          <QuickStatCard
            title="Customer Rating"
            value={agent?.customerSatisfactionRating ? `${agent.customerSatisfactionRating.toFixed(1)}/5` : 'N/A'}
            icon={Star}
            color="text-yellow-500"
          />
        </div>
      )}

      {/* Main Content */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="my-tickets">My Tickets</TabsTrigger>
          <TabsTrigger value="all-tickets">All Tickets</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* My Assigned Tickets */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <User className="w-5 h-5" />
                    My Assigned Tickets
                  </span>
                  <Badge variant="outline">{myTickets.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {myTickets.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>No tickets assigned</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {myTickets.map((ticket) => (
                      <TicketCard
                        key={ticket.ticketId}
                        ticket={ticket}
                        onClick={() => handleTicketClick(ticket)}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Urgent Tickets */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                    Urgent Tickets
                  </span>
                  <Badge variant="destructive">{urgentTickets.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {urgentTickets.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-300" />
                    <p>No urgent tickets</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {urgentTickets.map((ticket) => (
                      <TicketCard
                        key={ticket.ticketId}
                        ticket={ticket}
                        onClick={() => handleTicketClick(ticket)}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Unassigned Tickets */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Recent New Tickets
              </CardTitle>
            </CardHeader>
            <CardContent>
              {recentTickets.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>No new tickets</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {recentTickets.slice(0, 6).map((ticket) => (
                    <TicketCard
                      key={ticket.ticketId}
                      ticket={ticket}
                      onClick={() => handleTicketClick(ticket)}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="my-tickets">
          <TicketList
            userId=""
            isAgentView={true}
            agentId={agentId}
          />
        </TabsContent>

        <TabsContent value="all-tickets">
          <TicketList
            userId=""
            isAgentView={true}
          />
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          {/* Performance Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Resolution Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">
                  {agent?.averageResolutionTimeHours 
                    ? `${Math.round(agent.averageResolutionTimeHours)}h` 
                    : 'N/A'
                  }
                </div>
                <p className="text-sm text-gray-600">Average resolution time</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Active Tickets</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">
                  {agent?.currentTicketCount || 0}
                </div>
                <p className="text-sm text-gray-600">
                  of {agent?.maxConcurrentTickets || 10} max capacity
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Customer Rating</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <div className="text-2xl font-bold text-gray-900">
                    {agent?.customerSatisfactionRating 
                      ? agent.customerSatisfactionRating.toFixed(1)
                      : 'N/A'
                    }
                  </div>
                  <div className="flex">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`w-4 h-4 ${
                          agent?.customerSatisfactionRating && i < agent.customerSatisfactionRating
                            ? 'text-yellow-400 fill-current'
                            : 'text-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                </div>
                <p className="text-sm text-gray-600">Average customer rating</p>
              </CardContent>
            </Card>
          </div>

          {/* Agent Specializations */}
          {agent?.specializations && agent.specializations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
                  Specializations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {agent.specializations.map(spec => (
                    <Badge key={spec} variant="secondary">
                      {spec.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Weekly Performance Chart Placeholder */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Weekly Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <TrendingUp className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>Performance charts coming soon</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Ticket Detail Modal */}
      {selectedTicket && (
        <TicketDetailModal
          ticket={selectedTicket}
          isOpen={!!selectedTicket}
          onClose={() => setSelectedTicket(null)}
          onTicketUpdated={handleTicketUpdated}
          isAgentView={true}
          agentId={agentId}
        />
      )}
    </div>
  );
}