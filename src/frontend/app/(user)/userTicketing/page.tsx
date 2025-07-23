'use client';

import { useState, useRef, FormEvent } from 'react';
import { SearchBar } from '@/components/ui/searchBar';
import { Button } from '@/components/ui/button';
import { Plus, Send, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
  Input,
  Textarea,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/index';
import TicketTabs from '@/components/ui/user/ticketing/ticketTabs';
import { userTicketSchema } from '@/lib/api/schemas';

interface Ticket {
  id: string;
  title: string;
  customer: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  status: 'open' | 'in-progress' | 'pending' | 'resolved';
  assignee: string;
  created: string;
  updated: string;
  description: string;
  messages: number;
}

interface FormData {
  title: string;
  description: string;
  priority: '' | 'urgent' | 'high' | 'medium' | 'low';
  customer: string;
  assignee: string;
  status: 'open' | 'in-progress' | 'pending' | 'resolved';
}

const initialTickets: Ticket[] = [
  {
    id: '#12847',
    title: 'Payment processing error on checkout',
    customer: 'Alex Johnson',
    priority: 'urgent',
    status: 'open',
    assignee: 'Sarah Chen',
    created: '2 hours ago',
    updated: '5 min ago',
    description: 'Customer unable to complete payment during checkout process. Error occurs after entering payment details.',
    messages: 3,
  },
  {
    id: '#12846',
    title: 'Unable to access premium features',
    customer: 'Maria Garcia',
    priority: 'high',
    status: 'in-progress',
    assignee: 'Mike Johnson',
    created: '5 hours ago',
    updated: '15 min ago',
    description: 'Premium subscriber cannot access advanced dashboard features despite active subscription.',
    messages: 5,
  },
  {
    id: '#12845',
    title: 'Account verification issues',
    customer: 'David Chen',
    priority: 'medium',
    status: 'pending',
    assignee: 'Lisa Wang',
    created: '1 day ago',
    updated: '1 hour ago',
    description: 'User unable to verify account email address. Verification emails not being received.',
    messages: 2,
  },
];

const generateId = () => {
  return '#' + Math.floor(10000 + Math.random() * 90000).toString();
};

const priorityColors = {
  urgent: 'bg-red-500 text-white',
  high: 'bg-orange-500 text-white',
  medium: 'bg-yellow-500 text-white',
  low: 'bg-yellow-200 text-gray-900',
};

const statusColors = {
  open: 'bg-blue-100 text-blue-800',
  'in-progress': 'bg-orange-100 text-orange-800',
  pending: 'bg-yellow-100 text-yellow-800',
  resolved: 'bg-green-100 text-green-800',
};

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>(initialTickets);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState<FormData>({
    title: '',
    description: '',
    priority: '',
    customer: '',
    assignee: '',
    status: 'pending',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const validateForm = (data: FormData): boolean => {
    const result = userTicketSchema.safeParse(data);
    if (!result.success) {
      const newErrors = result.error.flatten().fieldErrors;
      setErrors({
        title: newErrors.title?.[0],
        description: newErrors.description?.[0],
        priority: newErrors.priority?.[0],
        customer: newErrors.customer?.[0],
        assignee: newErrors.assignee?.[0],
        status: newErrors.status?.[0],
      });
      return false;
    }
    setErrors({});
    return true;
  };

  const handleCreateTicket = (e?: FormEvent) => {
    if (e) e.preventDefault();
    if (!validateForm(formData)) return;

    const timestamp = new Date().toLocaleString('en-US', {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

    const newTicket: Ticket = {
      id: generateId(),
      title: formData.title,
      description: formData.description,
      priority: formData.priority as Ticket['priority'],
      status: formData.status,
      customer: formData.customer,
      assignee: formData.assignee,
      created: timestamp,
      updated: timestamp,
      messages: 0,
    };

    setTickets([...tickets, newTicket]);
    setFormData({
      title: '',
      description: '',
      priority: '',
      customer: '',
      assignee: '',
      status: 'open',
    });
    setOpen(false);
    if (closeButtonRef.current) {
      closeButtonRef.current.click();
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <main className="flex-1 p-6 pt-0 space-y-6">
        <div className="p-4 pt-0 flex justify-end items-center gap-4 flex-wrap">
          <SearchBar placeholder="Search tickets..." className="w-full sm:w-72" />
          <Dialog
            open={open}
            onOpenChange={(isOpen) => {
              setOpen(isOpen);
              if (!isOpen) {
                setFormData({
                  title: '',
                  description: '',
                  priority: '',
                  customer: '',
                  assignee: '',
                  status: 'open',
                });
                setErrors({});
              }
            }}
          >
            <DialogTrigger asChild>
              <Button className="bg-yellow-500 hover:bg-yellow-600 hover:scale-105 gap-2">
                <Plus className="h-4 w-4" />
                Create Ticket
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New Ticket</DialogTitle>
              </DialogHeader>
              <DialogClose
                ref={closeButtonRef}
                className="absolute right-4 top-4 rounded-md p-1 transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <X className="h-4 w-4 text-black dark:text-white" />
                <span className="sr-only">Close</span>
              </DialogClose>
              <form onSubmit={handleCreateTicket}>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Title</label>
                    <Input
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      placeholder="Enter ticket title"
                      className="mt-1"
                    />
                    {errors.title && <p className="text-sm text-red-500 mt-1">{errors.title}</p>}
                  </div>

                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Description</label>
                    <Textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Enter ticket description"
                      className="mt-1"
                      rows={4}
                    />
                    {errors.description && (
                      <p className="text-sm text-red-500 mt-1">{errors.description}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-muted-foreground">Priority</label>
                      <Select
                        value={formData.priority}
                        onValueChange={(value) => setFormData({ ...formData, priority: value })}
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue placeholder="Select priority" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="urgent">Urgent</SelectItem>
                        </SelectContent>
                      </Select>
                      {errors.priority && (
                        <p className="text-sm text-red-500 mt-1">{errors.priority}</p>
                      )}
                    </div>

                  </div>

                  <div className="flex justify-end mt-4">
                    <Button
                      type="submit"
                      className="bg-yellow-500 hover:bg-yellow-600 hover:scale-105 gap-2"
                    >
                      <Send className="h-4 w-4" />
                      Create Ticket
                    </Button>
                  </div>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        <TicketTabs
          tickets={tickets}
          priorityColors={priorityColors}
          statusColors={statusColors}
        />
      </main>
    </div>
  );
}
