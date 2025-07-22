import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Eye, MessageSquare, Clock } from "lucide-react";
import Link from "next/link"

const tickets = [
  {
    id: "#12847",
    title: "Payment processing error on checkout",
    customer: "Alex Johnson",
    status: "completed",
    lastUpdate: "2 min ago",
  },
  {
    id: "#12846",
    title: "Unable to access premium features",
    customer: "Maria Garcia", 
    status: "in-progress",
    lastUpdate: "15 min ago", 
  },
  {
    id: "#12845",
    title: "Account verification issues",
    customer: "David Chen",
    status: "pending",
    lastUpdate: "1 hour ago",
  }
];

const statusColors = {
  completed: "bg-green-100 text-green-800",
  "in-progress": "bg-orange-100 text-orange-800",
  pending: "bg-yellow-100 text-yellow-800",
  resolved: "bg-green-100 text-green-800"
};

export function TicketOverview() {
  return (
    <Card className="shadow-md hover:shadow-lg transition-shadow duration-200 dark:shadow-md dark:hover:shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg font-semibold">Recent Tickets</CardTitle>
        <Button asChild variant="outline" size="sm">
          <Link href="/ticketing">View All</Link>
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {tickets.map((ticket) => (
            <div key={ticket.id} className="p-4 hover:bg-muted/50 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-muted-foreground">{ticket.id}</span>
                    <Badge variant="secondary" className={`text-xs ${statusColors[ticket.status as keyof typeof statusColors]}`}>
                      {ticket.status}
                    </Badge>
                  </div>
                  <h4 className="font-medium text-foreground mb-1 truncate">{ticket.title}</h4>
                  <p className="text-sm text-muted-foreground">
                    {ticket.customer}
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {ticket.lastUpdate}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}