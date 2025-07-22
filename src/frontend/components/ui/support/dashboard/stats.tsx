import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Clock, Users, Ticket, CheckCircle } from "lucide-react";

const stats = [
  {
    title: "Active Tickets",
    value: "247",
    change: "+12",
    trend: "up",
    icon: Ticket,
    color: "text-yellow-500",
  },
  {
    title: "Resolved Today",
    value: "68",
    change: "+8",
    trend: "up",
    icon: CheckCircle,
    color: "text-green-600",
  },
  {
    title: "Avg Response Time",
    value: "2.4h",
    change: "-0.3h",
    trend: "down",
    icon: Clock,
    color: "text-orange-600",
  },
];

export function DashboardStats() {
  return (
    <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-3">
      {stats.map((stat) => (
        <Card key={stat.title} className="shadow-md hover:shadow-lg dark:shadow-md dark:hover:shadow-lg transition-shadow duration-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {stat.title}
            </CardTitle>
            <stat.icon className={`h-4 w-4 ${stat.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{stat.value}</div>
            <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
              {stat.trend === "up" && <TrendingUp className="h-3 w-3 text-green-600" />}
              {stat.trend === "down" && <TrendingDown className="h-3 w-3 text-red-600" />}
              <span className={stat.trend === "up" ? "text-green-600" : stat.trend === "down" ? "text-red-600" : ""}>
                {stat.change}
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}