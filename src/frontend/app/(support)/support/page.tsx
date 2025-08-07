"use client";

import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import { DashboardStats } from "@/components/ui/support/dashboard/stats"
import { TicketOverview } from "@/components/ui/support/dashboard/ticketOverview"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, TrendingUp, Users, Clock } from "lucide-react"
import { RecentActivity } from "@/components/ui/support/dashboard/recentActivity";
import  TicketPie  from "@/components/ui/support/dashboard/performance";
export default function Dashboard() {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true); // ensures client-side rendering only
  }, []);

  if (!mounted) return null; // prevent rendering until after hydration

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <main className="flex-1 p-3 space-y-3">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Good morning, Team!</h1>
          <p className="text-muted-foreground">
            Here's what's happening with your support team today.
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LEFT COLUMN - 2/3 width */}
          <div className="lg:col-span-2 space-y-6">
            <DashboardStats />
            <TicketOverview />
          </div>

          {/* RIGHT COLUMN - 1/3 width */}
          <div className="lg:col-span-1 space-y-6">
            {/* Recent Activity */}
            <Card className="shadow-md hover:shadow-lg transition-shadow duration-200 dark:shadow-md dark:hover:shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-yellow-500" />
                  Recent Activity
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <RecentActivity />
              </CardContent>
            </Card>

            {/* Team Performance */}
            <Card className="shadow-md hover:shadow-lg transition-shadow duration-200 dark:shadow-md dark:hover:shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-yellow-500" />
                  Team Performance
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <TicketPie />
              </CardContent>
            </Card>
          </div>

        </div>
      </main>
    </div>
  );
}
