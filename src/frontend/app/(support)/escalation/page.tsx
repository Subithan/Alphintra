"use client"
import { useState } from "react"
import { SearchBar } from "@/components/ui"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { EscalationRulesCard } from "@/components/ui/support/escaltion/escalationRulesCard"
import { RecentEscalationsCard } from "@/components/ui/support/escaltion/recentEscalationsCard"
import { AlertTriangle, Plus, Clock, Users, Flag } from "lucide-react"

const initialEscalationRules = [
  {
    id: "ESC001",
    name: "High Priority Timeout",
    description: "Escalate high priority tickets after 2 hours without response",
    trigger: "Response Time",
    condition: "2 hours",
    action: "Assign to Manager",
    status: "active" as "active",
    triggered: 24
  },
  {
    id: "ESC002",
    name: "Urgent Customer Escalation",
    description: "Immediately escalate urgent tickets from VIP customers",
    trigger: "Priority & Customer Tier",
    condition: "Urgent + VIP",
    action: "Notify Director",
    status: "active" as "active",
    triggered: 8
  },
  {
    id: "ESC003",
    name: "Multiple Reopens",
    description: "Escalate tickets reopened more than 3 times",
    trigger: "Reopen Count",
    condition: "> 3 reopens",
    action: "Senior Support Review",
    status: "inactive" as "inactive",
    triggered: 5
  }
]

const recentEscalations = [
  {
    ticket: "#12847",
    customer: "Alex Johnson",
    rule: "High Priority Timeout",
    escalatedTo: "Sarah Chen (Manager)",
    time: "2 hours ago",
    status: "pending" as "pending"
  },
  {
    ticket: "#12834",
    customer: "VIP Corp Inc",
    rule: "Urgent Customer Escalation",
    escalatedTo: "Mike Johnson (Director)",
    time: "4 hours ago",
    status: "resolved" as "resolved"
  }
]

export default function Escalation() {
  const [rules, setRules] = useState(initialEscalationRules)

  const toggleRuleStatus = (id: string) => {
    setRules(prev =>
      prev.map(rule =>
        rule.id === id ? { ...rule, status: rule.status === "active" ? "inactive" : "active" } : rule
      )
    )
  }

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <main className="flex-1 p-6 space-y-6">
        <div className="pt-0 flex justify-end items-center gap-4 flex-wrap">
          <SearchBar placeholder="Search Rule..." className="w-full sm:w-72" />

          <Dialog>
            <DialogTrigger asChild>
              <Button className="bg-yellow-500 hover:bg-yellow-500 hover:scale-105 gap-2 text-sm whitespace-nowrap">
                <Plus className="h-4 w-4" />New Rule
              </Button>
            </DialogTrigger>

            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Escalation Rule</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="rule-name">Rule Name</Label>
                    <Input id="rule-name" placeholder="Enter rule name" />
                  </div>
                  <div>
                    <Label htmlFor="trigger-type">Trigger Type</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select trigger" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="time">Response Time</SelectItem>
                        <SelectItem value="priority">Priority Level</SelectItem>
                        <SelectItem value="customer">Customer Tier</SelectItem>
                        <SelectItem value="reopens">Reopen Count</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <Label htmlFor="condition">Condition</Label>
                  <Input id="condition" placeholder="e.g., > 2 hours, Urgent, VIP" />
                </div>
                <div>
                  <Label htmlFor="action">Escalation Action</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select action" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="manager">Assign to Manager</SelectItem>
                      <SelectItem value="director">Notify Director</SelectItem>
                      <SelectItem value="senior">Senior Support Review</SelectItem>
                      <SelectItem value="external">External Escalation</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button variant="outline">Cancel</Button>
                  <Button>Create Rule</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card className="shadow-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
                <div>
                  <div className="text-2xl font-bold">37</div>
                  <p className="text-sm text-muted-foreground">Active Escalations</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="text-2xl font-bold">4.2h</div>
                  <p className="text-sm text-muted-foreground">Avg Resolution Time</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-green-600" />
                <div>
                  <div className="text-2xl font-bold">12</div>
                  <p className="text-sm text-muted-foreground">Rules Active</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Flag className="h-5 w-5 text-purple-600" />
                <div>
                  <div className="text-2xl font-bold">94%</div>
                  <p className="text-sm text-muted-foreground">Success Rate</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Cards */}
        <div className="grid gap-6 lg:grid-cols-2">
          <EscalationRulesCard escalationRules={rules} onToggle={toggleRuleStatus} />
          <RecentEscalationsCard recentEscalations={recentEscalations} />
        </div>
      </main>
    </div>
  )
}
