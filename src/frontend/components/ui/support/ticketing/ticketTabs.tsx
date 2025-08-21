'use client';

import { useState, useRef } from 'react';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent
} from "@/components/ui/tabs";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from "@/components/ui/card";
import {
  Badge,
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  Textarea
} from "@/components/ui/index";
import { User, MessageSquare, Clock, Send, Trash2, X } from "lucide-react";
import { ticketSchema } from '@/lib/api/schemas';

interface Ticket {
  id: string;
  title: string;
  description: string;
  priority: string;
  status: string;
  customer: string;
  assignee: string;
  created: string;
  updated: string;
  messages: number;
}

interface TicketTabsProps {
  tickets: Ticket[];
  statusColors: Record<string, string>;
  priorityColors: Record<string, string>;
}

const statuses = ["all", "open", "in-progress", "pending", "resolved"];

export default function TicketTabs({ tickets: initialTickets, statusColors, priorityColors }: TicketTabsProps) {
  const [tickets, setTickets] = useState<Ticket[]>(initialTickets);
  const [open, setOpen] = useState<boolean>(false);
  const [formData, setFormData] = useState<{ priority: string; status: string }>({ priority: '', status: '' });
  const [errors, setErrors] = useState<Partial<Record<keyof typeof formData, string>>>({});
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const validateForm = (data: { priority: string; status: string }): boolean => {
    const result = ticketSchema.safeParse(data);
    if (!result.success) {
      const newErrors = result.error.flatten().fieldErrors;
      setErrors({
        priority: newErrors.priority?.[0],
        status: newErrors.status?.[0],
      });
      return false;
    }
    setErrors({});
    return true;
  };

  const handleUpdateTicket = (ticketId: string) => {
    if (!validateForm(formData)) return;

    setTickets(tickets.map((ticket) =>
      ticket.id === ticketId
        ? {
            ...ticket,
            priority: formData.priority,
            status: formData.status,
            updated: new Date().toLocaleDateString('en-US', {
              month: 'short',
              day: '2-digit',
              year: 'numeric',
            }) + ' ' + new Date().toLocaleTimeString('en-US', {
              hour: '2-digit',
              minute: '2-digit',
            }),
          }
        : ticket
    ));

    setOpen(false);
    if (closeButtonRef.current) {
      closeButtonRef.current.click();
    }
  };

  const handleDeleteTicket = (ticketId: string) => {
    setTickets(tickets.filter((ticket) => ticket.id !== ticketId));
  };

  return (
    <Tabs defaultValue="all" className="space-y-6">
      <TabsList className="grid w-full grid-cols-5">
        {statuses.map((status) => (
          <TabsTrigger key={status} value={status}>
            {status === "all"
              ? "All Tickets"
              : status
                  .split("-")
                  .map((s) => s[0].toUpperCase() + s.slice(1))
                  .join(" ")}
          </TabsTrigger>
        ))}
      </TabsList>

      {statuses.map((status) => {
        const filteredTickets =
          status === "all"
            ? tickets
            : tickets.filter((ticket) => ticket.status === status);

        return (
          <TabsContent key={status} value={status} className="space-y-4">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>
                  {status === "all"
                    ? "All Support Tickets"
                    : `${status
                        .split("-")
                        .map((s) => s[0].toUpperCase() + s.slice(1))
                        .join(" ")} Tickets`}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {filteredTickets.length > 0 ? (
                  <div className="divide-y divide-border">
                    {filteredTickets.map((ticket) => (
                      <div
                        key={ticket.id}
                        className="p-6 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0 space-y-3">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-muted-foreground">
                                {ticket.id}
                              </span>
                              <Badge className={`text-xs text-gray-900 dark:text-white ${priorityColors[ticket.priority]}`}>
                                {ticket.priority}
                              </Badge>
                              <Badge className={`text-xs ${statusColors[ticket.status]}`}>
                                {ticket.status.replace('-', ' ')}
                              </Badge>
                            </div>
                            <div>
                              <h3 className="font-semibold text-foreground mb-1">
                                {ticket.title}
                              </h3>
                              <p className="text-sm text-muted-foreground line-clamp-2">
                                {ticket.description}
                              </p>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                              <div className="flex items-center gap-1">
                                <User className="h-3 w-3" />
                                {ticket.customer}
                              </div>
                              <div className="flex items-center gap-1">
                                <MessageSquare className="h-3 w-3" />
                                {ticket.messages} messages
                              </div>
                              <div className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                Updated {ticket.updated}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="text-right text-sm">
                              <div className="font-medium">Assigned to:</div>
                              <div className="text-muted-foreground">{ticket.assignee}</div>
                            </div>
                            <div className="flex gap-2">
                              <Dialog
                                onOpenChange={(isOpen) => {
                                  setOpen(isOpen);
                                  if (isOpen) {
                                    setFormData({ priority: ticket.priority, status: ticket.status });
                                    setErrors({});
                                  }
                                }}
                              >
                                <DialogTrigger asChild>
                                  <Button variant="outline" size="sm">
                                    View Details
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                                  <DialogHeader>
                                    <DialogTitle className="flex items-center gap-2 text-black dark:text-white">
                                      Ticket {ticket.id} - {ticket.title}
                                      <Badge className={`text-xs ${priorityColors[ticket.priority]}`}>
                                        {ticket.priority}
                                      </Badge>
                                    </DialogTitle>
                                  </DialogHeader>
                                  <DialogClose
                                    ref={closeButtonRef}
                                    className="absolute right-4 top-4 rounded-md p-1 transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
                                  >
                                    <X className="h-4 w-4 text-black dark:text-white" />
                                    <span className="sr-only">Close</span>
                                  </DialogClose>
                                  <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                      <div>
                                        <label className="text-sm font-medium text-muted-foreground">
                                          Customer
                                        </label>
                                        <p className="text-sm text-black dark:text-white">{ticket.customer}</p>
                                      </div>
                                      <div>
                                        <label className="text-sm font-medium text-muted-foreground">
                                          Assigned To
                                        </label>
                                        <p className="text-sm text-black dark:text-white">{ticket.assignee}</p>
                                      </div>
                                      <div>
                                        <label className="text-sm font-medium text-muted-foreground">
                                          Created
                                        </label>
                                        <p className="text-sm text-black dark:text-white">{ticket.created}</p>
                                      </div>
                                      <div>
                                        <label className="text-sm font-medium text-muted-foreground">
                                          Last Updated
                                        </label>
                                        <p className="text-sm text-black dark:text-white">{ticket.updated}</p>
                                      </div>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">
                                        Description
                                      </label>
                                      <p className="text-sm mt-1 p-3 bg-muted/50 rounded-lg text-black dark:text-white">
                                        {ticket.description}
                                      </p>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                      <div>
                                        <label className="text-sm font-medium text-muted-foreground">
                                          Priority
                                        </label>
                                        <Select
                                          value={formData.priority}
                                          onValueChange={(value) => setFormData({ ...formData, priority: value })}
                                        >
                                          <SelectTrigger className="mt-1">
                                            <SelectValue />
                                          </SelectTrigger>
                                          <SelectContent>
                                            <SelectItem value="low">Low</SelectItem>
                                            <SelectItem value="medium">Medium</SelectItem>
                                            <SelectItem value="high">High</SelectItem>
                                            <SelectItem value="urgent">Urgent</SelectItem>
                                          </SelectContent>
                                        </Select>
                                        {errors.priority && <p className="text-sm text-red-500 mt-1">{errors.priority}</p>}
                                      </div>
                                      <div>
                                        <label className="text-sm font-medium text-muted-foreground">
                                          Status
                                        </label>
                                        <Select
                                          value={formData.status}
                                          onValueChange={(value) => setFormData({ ...formData, status: value })}
                                        >
                                          <SelectTrigger className="mt-1">
                                            <SelectValue />
                                          </SelectTrigger>
                                          <SelectContent>
                                            <SelectItem value="open">Open</SelectItem>
                                            <SelectItem value="in-progress">In Progress</SelectItem>
                                            <SelectItem value="pending">Pending</SelectItem>
                                            <SelectItem value="resolved">Resolved</SelectItem>
                                          </SelectContent>
                                        </Select>
                                        {errors.status && <p className="text-sm text-red-500 mt-1">{errors.status}</p>}
                                      </div>
                                    </div>
                                    <div className="flex justify-end mt-2">
                                      <Button
                                        className="bg-yellow-500 hover:bg-yellow-500 hover:scale-105 gap-2"
                                        onClick={() => handleUpdateTicket(ticket.id)}
                                      >
                                        <Send className="h-4 w-4" />
                                        Send
                                      </Button>
                                    </div>
                                  </div>
                                </DialogContent>
                              </Dialog>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-sm text-muted-foreground">
                    No tickets found.
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        );
      })}
    </Tabs>
  );
}