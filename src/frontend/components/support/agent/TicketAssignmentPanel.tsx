'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { 
  Users, 
  Clock, 
  AlertTriangle, 
  TrendingUp, 
  User, 
  MessageSquare,
  ArrowRight,
  CheckCircle,
  X
} from 'lucide-react';
import { 
  customerSupportApi, 
  Ticket, 
  SupportAgent,
  UpdateTicketRequest,
  EscalationRequest,
  TicketStatus,
  AgentLevel,
  AgentStatus,
  formatStatus,
  formatPriority,
  getStatusColor,
  getPriorityColor
} from '@/lib/api/customer-support-api';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'react-hot-toast';

interface TicketAssignmentPanelProps {
  currentAgentId: string;
  currentAgentLevel: AgentLevel;
}

export default function TicketAssignmentPanel({ 
  currentAgentId, 
  currentAgentLevel 
}: TicketAssignmentPanelProps) {
  const [unassignedTickets, setUnassignedTickets] = useState<Ticket[]>([]);
  const [availableAgents, setAvailableAgents] = useState<SupportAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [assigningTicketId, setAssigningTicketId] = useState<string | null>(null);
  const [escalationModal, setEscalationModal] = useState<{
    ticket: Ticket | null;
    isOpen: boolean;
  }>({ ticket: null, isOpen: false });
  const [escalationReason, setEscalationReason] = useState('');
  const [targetLevel, setTargetLevel] = useState<AgentLevel | ''>('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load unassigned tickets
      const ticketsResponse = await customerSupportApi.getTickets(
        { status: TicketStatus.NEW }, 0, 20
      );
      setUnassignedTickets(ticketsResponse.content);

      // Load available agents
      const agents = await customerSupportApi.getAgents();
      const available = agents.filter(agent => 
        agent.status === AgentStatus.AVAILABLE && 
        agent.currentTicketCount < agent.maxConcurrentTickets
      );
      setAvailableAgents(available);
    } catch (error) {
      console.error('Failed to load assignment data:', error);
      toast.error('Failed to load assignment data');
    } finally {
      setLoading(false);
    }
  };

  const handleSelfAssign = async (ticketId: string) => {
    setAssigningTicketId(ticketId);
    try {
      const request: UpdateTicketRequest = {
        assignedAgentId: currentAgentId,
        status: TicketStatus.ASSIGNED
      };
      
      await customerSupportApi.updateTicket(ticketId, request);
      
      // Remove from unassigned list
      setUnassignedTickets(prev => prev.filter(t => t.ticketId !== ticketId));
      
      toast.success('Ticket assigned to you successfully');
    } catch (error) {
      console.error('Failed to assign ticket:', error);
      toast.error('Failed to assign ticket');
    } finally {
      setAssigningTicketId(null);
    }
  };

  const handleAssignToAgent = async (ticketId: string, agentId: string) => {
    try {
      const request: UpdateTicketRequest = {
        assignedAgentId: agentId,
        status: TicketStatus.ASSIGNED
      };
      
      await customerSupportApi.updateTicket(ticketId, request);
      
      // Remove from unassigned list
      setUnassignedTickets(prev => prev.filter(t => t.ticketId !== ticketId));
      
      toast.success('Ticket assigned successfully');
    } catch (error) {
      console.error('Failed to assign ticket:', error);
      toast.error('Failed to assign ticket');
    }
  };

  const handleEscalate = async () => {
    if (!escalationModal.ticket || !targetLevel || !escalationReason.trim()) {
      toast.error('Please fill in all escalation details');
      return;
    }

    try {
      const request: EscalationRequest = {
        targetLevel: targetLevel as AgentLevel,
        reason: escalationReason.trim()
      };
      
      await customerSupportApi.escalateTicket(escalationModal.ticket.ticketId, request);
      
      // Remove from unassigned list
      setUnassignedTickets(prev => prev.filter(t => t.ticketId !== escalationModal.ticket!.ticketId));
      
      setEscalationModal({ ticket: null, isOpen: false });
      setEscalationReason('');
      setTargetLevel('');
      
      toast.success('Ticket escalated successfully');
    } catch (error) {
      console.error('Failed to escalate ticket:', error);
      toast.error('Failed to escalate ticket');
    }
  };

  const openEscalationModal = (ticket: Ticket) => {
    setEscalationModal({ ticket, isOpen: true });
  };

  const closeEscalationModal = () => {
    setEscalationModal({ ticket: null, isOpen: false });
    setEscalationReason('');
    setTargetLevel('');
  };

  const getAvailableEscalationLevels = () => {
    const levels = Object.values(AgentLevel);
    const currentIndex = levels.indexOf(currentAgentLevel);
    return levels.slice(currentIndex + 1); // Only higher levels
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
      case 'URGENT':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'HIGH':
        return <TrendingUp className="w-4 h-4 text-orange-500" />;
      default:
        return <Clock className="w-4 h-4 text-blue-500" />;
    }
  };

  const getAgentLoadColor = (current: number, max: number) => {
    const percentage = (current / max) * 100;
    if (percentage >= 90) return 'text-red-600';
    if (percentage >= 70) return 'text-orange-600';
    return 'text-green-600';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardContent className="pt-6">
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                <div className="flex gap-2">
                  <div className="h-8 bg-gray-200 rounded w-20"></div>
                  <div className="h-8 bg-gray-200 rounded w-24"></div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Ticket Assignment</h2>
          <p className="text-gray-600">
            {unassignedTickets.length} unassigned ticket{unassignedTickets.length !== 1 ? 's' : ''} • {availableAgents.length} available agent{availableAgents.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button variant="outline" onClick={loadData}>
          <Clock className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Available Agents Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            Available Agents ({availableAgents.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {availableAgents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No agents available for assignment</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {availableAgents.map(agent => (
                <div key={agent.agentId} className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="font-medium text-sm">{agent.fullName}</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {agent.agentLevel}
                    </Badge>
                  </div>
                  
                  <div className="text-xs text-gray-600">
                    <div className={`font-medium ${getAgentLoadColor(agent.currentTicketCount, agent.maxConcurrentTickets)}`}>
                      {agent.currentTicketCount}/{agent.maxConcurrentTickets} tickets
                    </div>
                    
                    {agent.specializations && agent.specializations.length > 0 && (
                      <div className="mt-1">
                        <div className="flex flex-wrap gap-1">
                          {agent.specializations.slice(0, 2).map(spec => (
                            <Badge key={spec} variant="secondary" className="text-xs">
                              {spec.replace(/_/g, ' ').toLowerCase()}
                            </Badge>
                          ))}
                          {agent.specializations.length > 2 && (
                            <span className="text-xs text-gray-500">
                              +{agent.specializations.length - 2} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Unassigned Tickets */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Unassigned Tickets ({unassignedTickets.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {unassignedTickets.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-300" />
              <p>All tickets are assigned!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {unassignedTickets.map(ticket => (
                <div key={ticket.ticketId} className="border rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        {getPriorityIcon(ticket.priority)}
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
                      
                      <h3 className="font-medium text-gray-900 mb-1">
                        {ticket.title}
                      </h3>
                      
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {ticket.description}
                      </p>
                      
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>
                          Created {formatDistanceToNow(new Date(ticket.createdAt), { addSuffix: true })}
                        </span>
                        {ticket.userFullName && (
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {ticket.userFullName}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 pt-3 border-t">
                    <Button
                      size="sm"
                      onClick={() => handleSelfAssign(ticket.ticketId)}
                      disabled={assigningTicketId === ticket.ticketId}
                    >
                      {assigningTicketId === ticket.ticketId ? (
                        'Assigning...'
                      ) : (
                        <>
                          <User className="w-3 h-3 mr-1" />
                          Assign to Me
                        </>
                      )}
                    </Button>
                    
                    {availableAgents.length > 0 && (
                      <Select onValueChange={(agentId) => handleAssignToAgent(ticket.ticketId, agentId)}>
                        <SelectTrigger className="w-40">
                          <SelectValue placeholder="Assign to..." />
                        </SelectTrigger>
                        <SelectContent>
                          {availableAgents.map(agent => (
                            <SelectItem key={agent.agentId} value={agent.agentId}>
                              <div className="flex items-center justify-between w-full">
                                <span>{agent.fullName}</span>
                                <span className="text-xs text-gray-500 ml-2">
                                  {agent.currentTicketCount}/{agent.maxConcurrentTickets}
                                </span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                    
                    {getAvailableEscalationLevels().length > 0 && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEscalationModal(ticket)}
                      >
                        <ArrowRight className="w-3 h-3 mr-1" />
                        Escalate
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Escalation Modal */}
      <Dialog open={escalationModal.isOpen} onOpenChange={(open) => !open && closeEscalationModal()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Escalate Ticket #{escalationModal.ticket?.ticketId}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="targetLevel">Target Level</Label>
              <Select value={targetLevel} onValueChange={setTargetLevel}>
                <SelectTrigger className="mt-1">
                  <SelectValue placeholder="Select escalation level" />
                </SelectTrigger>
                <SelectContent>
                  {getAvailableEscalationLevels().map(level => (
                    <SelectItem key={level} value={level}>
                      {level.replace('_', ' ')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="escalationReason">Escalation Reason</Label>
              <Textarea
                id="escalationReason"
                value={escalationReason}
                onChange={(e) => setEscalationReason(e.target.value)}
                placeholder="Explain why this ticket needs escalation..."
                rows={3}
                className="mt-1"
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={closeEscalationModal}>
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button onClick={handleEscalate} disabled={!targetLevel || !escalationReason.trim()}>
                <TrendingUp className="w-4 h-4 mr-2" />
                Escalate Ticket
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}