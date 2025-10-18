'use client';

import { useState, useRef } from 'react';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui/tabs';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
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
} from '@/components/ui/index';
import { Clock, X } from 'lucide-react';
import { ticketSchema } from '@/lib/api/schemas';

interface Ticket {
  id: string;
  title: string;
  description: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  status: 'open' | 'in-progress' | 'pending' | 'resolved';
  customer: string;
  assignee: string;
  created: string;
  updated: string;
  messages: number;
}

interface TicketTabsProps {
  tickets: Ticket[];
  statusColors: Record<Ticket['status'], string>;
  priorityColors: Record<Ticket['priority'], string>;
  setTickets: React.Dispatch<React.SetStateAction<Ticket[]>>;
}

type TicketUpdateForm = {
  priority: Ticket['priority'] | '';
  status: Ticket['status'] | '';
};

const statuses: Array<'all' | Ticket['status']> = ['all', 'open', 'in-progress', 'pending', 'resolved'];

export default function TicketTabs({ tickets, statusColors, priorityColors, setTickets }: TicketTabsProps) {
  const [open, setOpen] = useState<boolean>(false);
  const [currentTicketId, setCurrentTicketId] = useState<string | null>(null);
  const [formData, setFormData] = useState<TicketUpdateForm>({ priority: '', status: '' });
  const [errors, setErrors] = useState<Partial<Record<keyof TicketUpdateForm, string>>>({});
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const validateForm = (data: TicketUpdateForm): boolean => {
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

  const handleUpdateTicket = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentTicketId || !validateForm(formData)) return;

    setTickets(
      tickets.map((ticket) =>
        ticket.id === currentTicketId
          ? {
              ...ticket,
              priority: formData.priority as Ticket['priority'],
              status: formData.status as Ticket['status'],
              updated: new Date().toLocaleDateString('en-US', {
                month: 'short',
                day: '2-digit',
                year: 'numeric',
              }) +
                ' ' +
                new Date().toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit',
                }),
            }
          : ticket
      )
    );

    setOpen(false);
    setCurrentTicketId(null);
    setFormData({ priority: '', status: '' });
    if (closeButtonRef.current) {
      closeButtonRef.current.click();
    }
  };

  return (
    <Tabs defaultValue="all" className="space-y-6">
      <TabsList className="grid w-full grid-cols-5">
        {statuses.map((status) => (
          <TabsTrigger key={status} value={status}>
            {status === 'all'
              ? 'All Tickets'
              : status
                  .split('-')
                  .map((s) => s[0].toUpperCase() + s.slice(1))
                  .join(' ')}
          </TabsTrigger>
        ))}
      </TabsList>

      {statuses.map((status) => {
        const filteredTickets =
          status === 'all'
            ? tickets
            : tickets.filter((ticket) => ticket.status === status);

        return (
          <TabsContent key={status} value={status} className="space-y-4">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>
                  {status === 'all'
                    ? 'All Support Tickets'
                    : `${status
                        .split('-')
                        .map((s) => s[0].toUpperCase() + s.slice(1))
                        .join(' ')} Tickets`}
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
                                <Clock className="h-3 w-3" />
                                Updated {ticket.updated}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Dialog
                              open={open && currentTicketId === ticket.id}
                              onOpenChange={(isOpen) => {
                                setOpen(isOpen);
                                if (isOpen) {
                                  setCurrentTicketId(ticket.id);
                                  setFormData({ priority: ticket.priority, status: ticket.status });
                                  setErrors({});
                                } else {
                                  setCurrentTicketId(null);
                                  setFormData({ priority: '', status: '' });
                                }
                              }}
                            >
                              <DialogTrigger asChild>
                                <Button variant="outline" size="sm">
                                  View
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                                <DialogHeader>
                                  <DialogTitle className="flex items-center gap-2 text-black dark:text-white">
                                    {ticket.title}
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
                                <form onSubmit={handleUpdateTicket} className="space-y-4">
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">
                                        Description
                                      </label>
                                      <p className="text-sm mt-1">{ticket.description}</p>
                                    </div>

                                  </div>
                                  <div className="flex justify-end mt-4">
                                    {/* No submit button as per original UI */}
                                  </div>
                                </form>
                              </DialogContent>
                            </Dialog>
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
