"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Activity } from "lucide-react";

const activityList = [
  {
    color: "bg-green-500",
    title: "Ticket #12847 resolved",
    subtitle: "by Sarah • 5 min ago",
  },
  {
    color: "bg-blue-500",
    title: "New escalation rule created",
    subtitle: "by Mike • 15 min ago",
  },
  {
    color: "bg-orange-500",
    title: "Knowledge base article updated",
    subtitle: "by Lisa • 1 hour ago",
  },
];

export function RecentActivity() {
  return (
      <div className="space-y-3">
        {activityList.map((activity, index) => (
          <div key={index} className="flex items-start gap-3">
            <div
              className={`w-2 h-2 ${activity.color} rounded-full mt-2 flex-shrink-0`}
            ></div>
            <div className="text-sm">
              <p className="font-medium">{activity.title}</p>
              <p className="text-muted-foreground text-xs">{activity.subtitle}</p>
            </div>
          </div>
        ))}
      </div>
  );
}
