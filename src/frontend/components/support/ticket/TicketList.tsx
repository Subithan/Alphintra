'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Search, Filter, Clock, MessageSquare, User, Calendar, RefreshCw } from 'lucide-react';
import { 
  customerSupportApi, 
  Ticket, 
  TicketFilter, 
  TicketStatus, 
  TicketPriority, 
  TicketCategory,
  formatStatus,
  formatPriority,
  formatCategory,
  getStatusColor,
  getPriorityColor
} from '@/lib/api/customer-support-api';
import { formatDistanceToNow } from 'date-fns';
import CreateTicketModal from './CreateTicketModal';
import TicketDetailModal from './TicketDetailModal';
import { toast } from 'react-hot-toast';

interface TicketListProps {
  userId: string;
  userEmail?: string;
  isAgentView?: boolean;
  agentId?: string;
}

export default function TicketList({ userId, userEmail, isAgentView = false, agentId }: TicketListProps) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<TicketFilter>({});
  const [statusFilter, setStatusFilter] = useState<TicketStatus | 'ALL'>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<TicketPriority | 'ALL'>('ALL');
  const [categoryFilter, setCategoryFilter] = useState<TicketCategory | 'ALL'>('ALL');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [totalElements, setTotalElements] = useState(0);

  const loadTickets = async (currentPage = 0, currentFilter = filter) => {
    setLoading(true);
    try {
      const filterParams: TicketFilter = {
        ...currentFilter,
        ...(isAgentView && agentId ? { agentId } : { userId }),
        ...(statusFilter !== 'ALL' && { status: statusFilter as TicketStatus }),
        ...(priorityFilter !== 'ALL' && { priority: priorityFilter as TicketPriority }),
        ...(categoryFilter !== 'ALL' && { category: categoryFilter as TicketCategory }),
        ...(searchTerm && { searchTerm })
      };

      const response = await customerSupportApi.getTickets(filterParams, currentPage, 20);
      setTickets(response.content);
      setTotalPages(response.totalPages);
      setTotalElements(response.totalElements);
      setPage(currentPage);
    } catch (error) {
      console.error('Failed to load tickets:', error);
      toast.error('Failed to load tickets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, [userId, agentId, isAgentView, statusFilter, priorityFilter, categoryFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadTickets(0);
  };

  const handleRefresh = () => {
    loadTickets(page);
  };

  const handleTicketCreated = () => {
    loadTickets();
  };

  const handleTicketClick = (ticket: Ticket) => {
    setSelectedTicket(ticket);
  };

  const handleTicketUpdated = (updatedTicket: Ticket) => {
    setTickets(prev => prev.map(t => t.ticketId === updatedTicket.ticketId ? updatedTicket : t));
    setSelectedTicket(updatedTicket);
  };

  const getRelativeTime = (dateString: string) => {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  };

  const getTicketIcon = (status: TicketStatus) => {
    switch (status) {
      case TicketStatus.NEW:
        return <MessageSquare className="w-4 h-4" />;
      case TicketStatus.IN_PROGRESS:
        return <Clock className="w-4 h-4" />;
      case TicketStatus.ASSIGNED:
        return <User className="w-4 h-4" />;
      default:
        return <MessageSquare className="w-4 h-4" />;
    }
  };

  const EmptyState = () => (
    <div className="text-center py-12">
      <MessageSquare className="w-12 h-12 mx-auto text-gray-400" />
      <h3 className="mt-4 text-lg font-medium text-gray-900">No tickets found</h3>
      <p className="mt-2 text-gray-600">
        {isAgentView 
          ? "No tickets match your current filters"
          : "You haven't created any support tickets yet"
        }
      </p>
      {!isAgentView && (
        <Button onClick={() => setShowCreateModal(true)} className="mt-4">
          <Plus className="w-4 h-4 mr-2" />
          Create Your First Ticket
        </Button>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {isAgentView ? 'Assigned Tickets' : 'Support Tickets'}
          </h1>
          <p className="text-gray-600">
            {totalElements > 0 
              ? `${totalElements} ticket${totalElements !== 1 ? 's' : ''} found`
              : 'No tickets to display'
            }
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {!isAgentView && (
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              New Ticket
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <Input
                    placeholder="Search tickets..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Button type="submit" disabled={loading}>
                <Search className="w-4 h-4 mr-2" />
                Search
              </Button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as TicketStatus | 'ALL')}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Statuses</SelectItem>
                    {Object.values(TicketStatus).map(status => (
                      <SelectItem key={status} value={status}>
                        {formatStatus(status)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Select value={priorityFilter} onValueChange={(value) => setPriorityFilter(value as TicketPriority | 'ALL')}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Priorities" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Priorities</SelectItem>
                    {Object.values(TicketPriority).map(priority => (
                      <SelectItem key={priority} value={priority}>
                        {formatPriority(priority)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Select value={categoryFilter} onValueChange={(value) => setCategoryFilter(value as TicketCategory | 'ALL')}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Categories" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All Categories</SelectItem>
                    {Object.values(TicketCategory).map(category => (
                      <SelectItem key={category} value={category}>
                        {formatCategory(category)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Ticket List */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="animate-pulse space-y-4">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                  <div className="flex gap-2">
                    <div className="h-6 bg-gray-200 rounded w-16"></div>
                    <div className="h-6 bg-gray-200 rounded w-20"></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : tickets.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-4">
          {tickets.map((ticket) => (
            <Card 
              key={ticket.ticketId} 
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => handleTicketClick(ticket)}
            >
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      {getTicketIcon(ticket.status)}
                      <span className="text-sm font-medium text-gray-600">
                        #{ticket.ticketId}
                      </span>
                      <Badge className={getStatusColor(ticket.status)}>
                        {formatStatus(ticket.status)}
                      </Badge>
                      <Badge className={getPriorityColor(ticket.priority)}>
                        {formatPriority(ticket.priority)}
                      </Badge>
                    </div>
                    
                    <h3 className="text-lg font-medium text-gray-900 truncate mb-1">
                      {ticket.title}
                    </h3>
                    
                    <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                      {ticket.description}
                    </p>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        {getRelativeTime(ticket.createdAt)}
                      </div>
                      
                      {ticket.assignedAgentName && (
                        <div className="flex items-center gap-1">
                          <User className="w-4 h-4" />
                          {ticket.assignedAgentName}
                        </div>
                      )}
                      
                      {ticket.communicationCount && ticket.communicationCount > 0 && (
                        <div className="flex items-center gap-1">
                          <MessageSquare className="w-4 h-4" />
                          {ticket.communicationCount} message{ticket.communicationCount !== 1 ? 's' : ''}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="ml-4 flex-shrink-0">
                    <Badge variant="outline">
                      {formatCategory(ticket.category)}
                    </Badge>
                    {ticket.hasUnreadMessages && (
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 ml-auto"></div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            onClick={() => loadTickets(page - 1)}
            disabled={page === 0 || loading}
          >
            Previous
          </Button>
          
          <span className="flex items-center px-3 py-2 text-sm text-gray-600">
            Page {page + 1} of {totalPages}
          </span>
          
          <Button
            variant="outline"
            onClick={() => loadTickets(page + 1)}
            disabled={page >= totalPages - 1 || loading}
          >
            Next
          </Button>
        </div>
      )}

      {/* Modals */}
      <CreateTicketModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onTicketCreated={handleTicketCreated}
        userId={userId}
        userEmail={userEmail}
      />

      {selectedTicket && (
        <TicketDetailModal
          ticket={selectedTicket}
          isOpen={!!selectedTicket}
          onClose={() => setSelectedTicket(null)}
          onTicketUpdated={handleTicketUpdated}
          isAgentView={isAgentView}
          agentId={agentId}
        />
      )}
    </div>
  );
}