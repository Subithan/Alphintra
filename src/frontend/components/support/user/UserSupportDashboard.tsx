'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, MessageSquare, Clock, CheckCircle, AlertTriangle, HelpCircle, Zap } from 'lucide-react';
import { 
  customerSupportApi, 
  Ticket, 
  TicketStats,
  TicketStatus,
  formatStatus,
  formatPriority,
  getStatusColor,
  getPriorityColor
} from '@/lib/api/customer-support-api';
import { formatDistanceToNow } from 'date-fns';
import CreateTicketModal from '../ticket/CreateTicketModal';
import TicketList from '../ticket/TicketList';
import { toast } from 'react-hot-toast';

interface UserSupportDashboardProps {
  userId: string;
  userEmail?: string;
  userName?: string;
}

export default function UserSupportDashboard({ userId, userEmail, userName }: UserSupportDashboardProps) {
  const [recentTickets, setRecentTickets] = useState<Ticket[]>([]);
  const [stats, setStats] = useState<TicketStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [view, setView] = useState<'dashboard' | 'all-tickets'>('dashboard');

  useEffect(() => {
    loadDashboardData();
  }, [userId]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load recent tickets (last 5)
      const ticketsResponse = await customerSupportApi.getMyTickets(undefined, 0, 5);
      setRecentTickets(ticketsResponse.content);

      // Load user stats
      const statsResponse = await customerSupportApi.getTicketStats();
      setStats(statsResponse);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleTicketCreated = () => {
    loadDashboardData();
  };

  const getStatusIcon = (status: TicketStatus) => {
    switch (status) {
      case TicketStatus.NEW:
        return <MessageSquare className="w-5 h-5" />;
      case TicketStatus.IN_PROGRESS:
        return <Clock className="w-5 h-5" />;
      case TicketStatus.RESOLVED:
      case TicketStatus.CLOSED:
        return <CheckCircle className="w-5 h-5" />;
      case TicketStatus.ESCALATED:
        return <AlertTriangle className="w-5 h-5" />;
      default:
        return <MessageSquare className="w-5 h-5" />;
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  if (view === 'all-tickets') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button variant="outline" onClick={() => setView('dashboard')}>
            ← Back to Dashboard
          </Button>
        </div>
        <TicketList userId={userId} userEmail={userEmail} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {getGreeting()}{userName ? `, ${userName}` : ''}
          </h1>
          <p className="text-gray-600 mt-1">
            How can we help you today? Access your support tickets and get assistance.
          </p>
        </div>
        
        <Button onClick={() => setShowCreateModal(true)} size="lg">
          <Plus className="w-5 h-5 mr-2" />
          Create Ticket
        </Button>
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
      ) : stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Tickets</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalTickets}</p>
                </div>
                <MessageSquare className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Open Tickets</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.openTickets}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Resolved</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.resolvedTickets}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Resolution</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(stats.averageResolutionTimeHours)}h
                  </p>
                </div>
                <Zap className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5" />
            Quick Actions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button 
              variant="outline" 
              className="h-20 flex flex-col gap-2"
              onClick={() => setShowCreateModal(true)}
            >
              <Plus className="w-6 h-6" />
              <span>Create New Ticket</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-20 flex flex-col gap-2"
              onClick={() => setView('all-tickets')}
            >
              <MessageSquare className="w-6 h-6" />
              <span>View All Tickets</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-20 flex flex-col gap-2"
              onClick={() => window.open('/help', '_blank')}
            >
              <HelpCircle className="w-6 h-6" />
              <span>Browse Help Center</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Tickets */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Recent Tickets
            </CardTitle>
            {recentTickets.length > 0 && (
              <Button variant="outline" onClick={() => setView('all-tickets')}>
                View All
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="animate-pulse border rounded-lg p-4">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                  <div className="flex gap-2">
                    <div className="h-6 bg-gray-200 rounded w-16"></div>
                    <div className="h-6 bg-gray-200 rounded w-20"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : recentTickets.length === 0 ? (
            <div className="text-center py-12">
              <MessageSquare className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No tickets yet</h3>
              <p className="text-gray-600 mb-4">
                You haven't created any support tickets. Get help by creating your first ticket.
              </p>
              <Button onClick={() => setShowCreateModal(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Ticket
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {recentTickets.map((ticket) => (
                <div 
                  key={ticket.ticketId} 
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(ticket.status)}
                      <span className="text-sm font-medium text-gray-600">
                        #{ticket.ticketId}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(ticket.status)}`}>
                        {formatStatus(ticket.status)}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(ticket.priority)}`}>
                        {formatPriority(ticket.priority)}
                      </span>
                    </div>
                  </div>
                  
                  <h3 className="font-medium text-gray-900 mb-1">
                    {ticket.title}
                  </h3>
                  
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {ticket.description}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Created {formatDistanceToNow(new Date(ticket.createdAt), { addSuffix: true })}</span>
                    {ticket.hasUnreadMessages && (
                      <span className="flex items-center gap-1 text-blue-600 font-medium">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        New messages
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Common Issues */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5" />
            Common Issues
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Trading Issues</h4>
              <div className="space-y-2 text-sm">
                <button className="text-left text-blue-600 hover:text-blue-800 block">
                  Cannot connect to trading platform
                </button>
                <button className="text-left text-blue-600 hover:text-blue-800 block">
                  Strategy execution problems
                </button>
                <button className="text-left text-blue-600 hover:text-blue-800 block">
                  Broker integration issues
                </button>
              </div>
            </div>
            
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Account & Billing</h4>
              <div className="space-y-2 text-sm">
                <button className="text-left text-blue-600 hover:text-blue-800 block">
                  Subscription questions
                </button>
                <button className="text-left text-blue-600 hover:text-blue-800 block">
                  Payment issues
                </button>
                <button className="text-left text-blue-600 hover:text-blue-800 block">
                  Account verification
                </button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create Ticket Modal */}
      <CreateTicketModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onTicketCreated={handleTicketCreated}
        userId={userId}
        userEmail={userEmail}
      />
    </div>
  );
}