import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent
} from "@/components/ui/tabs"
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from "@/components/ui/card"
import {
  Badge,
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  Textarea
} from "@/components/ui/index"
import { User, MessageSquare, Clock, Send } from "lucide-react"

interface Ticket {
  id: string
  title: string
  description: string
  priority: string
  status: string
  customer: string
  assignee: string
  created: string
  updated: string
  messages: number
}

interface TicketTabsProps {
  tickets: Ticket[]
  statusColors: Record<string, string>
  priorityColors: Record<string, string>
}

const statuses = ["all", "open", "in-progress", "pending", "resolved"]

export default function TicketTabs({ tickets, statusColors, priorityColors }: TicketTabsProps) {
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
            : tickets.filter((ticket) => ticket.status === status)

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
                              <Badge className={`text-xs ${priorityColors[ticket.priority]}`}>
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
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button variant="outline" size="sm">
                                  View Details
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                                <DialogHeader>
                                  <DialogTitle className="flex items-center gap-2">
                                    Ticket {ticket.id} - {ticket.title}
                                    <Badge className={`text-xs ${priorityColors[ticket.priority]}`}>
                                      {ticket.priority}
                                    </Badge>
                                  </DialogTitle>
                                </DialogHeader>
                                <div className="grid gap-6 py-4">
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">
                                        Customer
                                      </label>
                                      <p className="text-sm">{ticket.customer}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">
                                        Assigned To
                                      </label>
                                      <p className="text-sm">{ticket.assignee}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">
                                        Created
                                      </label>
                                      <p className="text-sm">{ticket.created}</p>
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">
                                        Last Updated
                                      </label>
                                      <p className="text-sm">{ticket.updated}</p>
                                    </div>
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium text-muted-foreground">
                                      Description
                                    </label>
                                    <p className="text-sm mt-1 p-3 bg-muted/50 rounded-lg">
                                      {ticket.description}
                                    </p>
                                  </div>
                                  <div className="grid grid-cols-2 gap-4">
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">
                                        Priority
                                      </label>
                                      <Select defaultValue={ticket.priority}>
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
                                    </div>
                                    <div>
                                      <label className="text-sm font-medium text-muted-foreground">
                                        Status
                                      </label>
                                      <Select defaultValue={ticket.status}>
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
                                    </div>
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium text-muted-foreground">
                                      Add Response
                                    </label>
                                    <Textarea
                                      placeholder="Type your response here..."
                                      className="mt-1 min-h-[100px]"
                                    />
                                    <div className="flex justify-end mt-2">
                                      <Button className="gap-2">
                                        <Send className="h-4 w-4" />
                                        Send Response
                                      </Button>
                                    </div>
                                  </div>
                                </div>
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
        )
      })}
    </Tabs>
  )
}
