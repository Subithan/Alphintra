'use client'

import { SearchBar } from '@/components/ui/searchBar'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import TicketTabs from '@/components/ui/support/ticketing/ticketTabs'

const tickets = [
  {
    id: '#12847',
    title: 'Payment processing error on checkout',
    customer: 'Alex Johnson',
    priority: 'urgent',
    status: 'open',
    assignee: 'Sarah Chen',
    created: '2 hours ago',
    updated: '5 min ago',
    description:
      'Customer unable to complete payment during checkout process. Error occurs after entering payment details.',
    messages: 3
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
    description:
      'Premium subscriber cannot access advanced dashboard features despite active subscription.',
    messages: 5
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
    description:
      'User unable to verify account email address. Verification emails not being received.',
    messages: 2
  }
]

const priorityColors = {
  urgent: 'bg-support-urgent text-white',
  high: 'bg-support-high text-white',
  medium: 'bg-support-medium text-white',
  low: 'bg-support-low text-white',
}

const statusColors = {
  open: 'bg-blue-100 text-blue-800',
  'in-progress': 'bg-orange-100 text-orange-800',
  pending: 'bg-yellow-100 text-yellow-800',
  resolved: 'bg-green-100 text-green-800',
}

export default function TicketsPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <main className="flex-1 p-6 pt-0 space-y-6">
        <div className="p-4 pt-0 flex justify-end items-center gap-4 flex-wrap">
          <SearchBar placeholder="Search tickets..." className="w-full sm:w-72" />
          <Button className="bg-yellow-500 hover:bg-yellow-500 hover:scale-105 gap-2 text-sm whitespace-nowrap">
            <Plus className="h-4 w-4" />New Ticket
          </Button>
        </div>
        {/* Ticket Tabs */}
        <TicketTabs
          tickets={tickets}
          priorityColors={priorityColors}
          statusColors={statusColors}
        />
      </main>
    </div>
  )
}
