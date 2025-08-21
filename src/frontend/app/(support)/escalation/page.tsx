'use client';

import { useState, useRef } from "react";
import { SearchBar } from "@/components/ui";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EscalationRulesCard } from "@/components/ui/support/escaltion/escalationRulesCard";
import { RecentEscalationsCard } from "@/components/ui/support/escaltion/recentEscalationsCard";
import { AlertTriangle, Plus, Clock, Users, Flag, X } from "lucide-react";
import { escalationRuleSchema } from "@/lib/api/schemas";

interface EscalationRule {
  id: string;
  name: string;
  description: string;
  trigger: string;
  condition: string;
  action: string;
  status: "active" | "inactive";
  triggered: number;
}

const initialEscalationRules: EscalationRule[] = [
  {
    id: "ESC001",
    name: "High Priority Timeout",
    description: "Escalate high priority tickets after 2 hours without response",
    trigger: "Response Time",
    condition: "2 hours",
    action: "Assign to Manager",
    status: "active",
    triggered: 24,
  },
  {
    id: "ESC002",
    name: "Urgent Customer Escalation",
    description: "Immediately escalate urgent tickets from VIP customers",
    trigger: "Priority Level",
    condition: "Urgent + VIP",
    action: "Notify Director",
    status: "active",
    triggered: 8,
  },
  {
    id: "ESC003",
    name: "Multiple Reopens",
    description: "Escalate tickets reopened more than 3 times",
    trigger: "Reopen Count",
    condition: "> 3 reopens",
    action: "Senior Support Review",
    status: "inactive",
    triggered: 5,
  },
];

const recentEscalations = [
  {
    ticket: "#12847",
    customer: "Alex Johnson",
    rule: "High Priority Timeout",
    escalatedTo: "Sarah Chen (Manager)",
    time: "2 hours ago",
    status: "pending" as "pending",
  },
  {
    ticket: "#12834",
    customer: "VIP Corp Inc",
    rule: "Urgent Customer Escalation",
    escalatedTo: "Mike Johnson (Director)",
    time: "4 hours ago",
    status: "resolved" as "resolved",
  },
];

export default function Escalation() {
  const [rules, setRules] = useState<EscalationRule[]>(initialEscalationRules);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    trigger: 'Response Time',
    condition: '',
    action: 'Assign to Manager',
    status: 'active' as 'active' | 'inactive',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof typeof formData, string>>>({});
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const validateForm = (): boolean => {
    const result = escalationRuleSchema.safeParse(formData);
    if (!result.success) {
      const newErrors = result.error.flatten().fieldErrors;
      setErrors({
        name: newErrors.name?.[0],
        description: newErrors.description?.[0],
        trigger: newErrors.trigger?.[0],
        condition: newErrors.condition?.[0],
        action: newErrors.action?.[0],
        status: newErrors.status?.[0],
      });
      return false;
    }
    setErrors({});
    return true;
  };

  const handleAddRule = () => {
    if (!validateForm()) return;

    setRules([
      ...rules,
      {
        ...formData,
        id: `ESC${(Math.floor(Math.random() * 1000) + 1).toString().padStart(3, '0')}`,
        triggered: 0,
      },
    ]);

    setFormData({
      name: '',
      description: '',
      trigger: 'Response Time',
      condition: '',
      action: 'Assign to Manager',
      status: 'active',
    });
    setErrors({});
    setOpen(false);
    if (closeButtonRef.current) {
      closeButtonRef.current.click();
    }
  };

  const toggleRuleStatus = (id: string) => {
    setRules(prev =>
      prev.map(rule =>
        rule.id === id ? { ...rule, status: rule.status === "active" ? "inactive" : "active" } : rule
      )
    );
  };

  const handleDeleteRule = (id: string) => {
    setRules(rules.filter((rule) => rule.id !== id));
  };

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <main className="flex-1 p-6 space-y-6">
        <div className="pt-0 flex justify-end items-center gap-4 flex-wrap">
          <SearchBar placeholder="Search Rule..." className="w-full sm:w-72" />
          <Dialog
            open={open}
            onOpenChange={(isOpen) => {
              setOpen(isOpen);
              if (!isOpen) {
                setFormData({
                  name: '',
                  description: '',
                  trigger: 'Response Time',
                  condition: '',
                  action: 'Assign to Manager',
                  status: 'active',
                });
                setErrors({});
              }
            }}
          >
            <DialogTrigger asChild>
              <Button className="bg-yellow-500 hover:bg-yellow-500 hover:scale-105 gap-2 text-sm whitespace-nowrap">
                <Plus className="h-4 w-4" /> New Rule
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle className="text-black dark:text-white">Create Escalation Rule</DialogTitle>
              </DialogHeader>
              <DialogClose
                ref={closeButtonRef}
                className="absolute right-4 top-4 rounded-md p-1 transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <X className="h-4 w-4 text-black dark:text-white" />
                <span className="sr-only">Close</span>
              </DialogClose>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="rule-name">Rule Name</Label>
                    <Input
                      id="rule-name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Enter rule name"
                    />
                    {errors.name && <p className="text-sm text-red-500 mt-1">{errors.name}</p>}
                  </div>
                  <div>
                    <Label htmlFor="trigger-type">Trigger Type</Label>
                    <Select
                      value={formData.trigger}
                      onValueChange={(value) => setFormData({ ...formData, trigger: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select trigger" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Response Time">Response Time</SelectItem>
                        <SelectItem value="Priority Level">Priority Level</SelectItem>
                        <SelectItem value="Customer Tier">Customer Tier</SelectItem>
                        <SelectItem value="Reopen Count">Reopen Count</SelectItem>
                      </SelectContent>
                    </Select>
                    {errors.trigger && <p className="text-sm text-red-500 mt-1">{errors.trigger}</p>}
                  </div>
                </div>
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Enter rule description"
                  />
                  {errors.description && <p className="text-sm text-red-500 mt-1">{errors.description}</p>}
                </div>
                <div>
                  <Label htmlFor="condition">Condition</Label>
                  <Input
                    id="condition"
                    value={formData.condition}
                    onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                    placeholder="e.g., > 2 hours, Urgent, VIP"
                  />
                  {errors.condition && <p className="text-sm text-red-500 mt-1">{errors.condition}</p>}
                </div>
                <div>
                  <Label htmlFor="action">Escalation Action</Label>
                  <Select
                    value={formData.action}
                    onValueChange={(value) => setFormData({ ...formData, action: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select action" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Assign to Manager">Assign to Manager</SelectItem>
                      <SelectItem value="Notify Director">Notify Director</SelectItem>
                      <SelectItem value="Senior Support Review">Senior Support Review</SelectItem>
                      <SelectItem value="External Escalation">External Escalation</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.action && <p className="text-sm text-red-500 mt-1">{errors.action}</p>}
                </div>
                <div>
                  <Label htmlFor="status">Status</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(value) => setFormData({ ...formData, status: value as 'active' | 'inactive' })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.status && <p className="text-sm text-red-500 mt-1">{errors.status}</p>}
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <DialogClose asChild>
                    <Button variant="outline">Cancel</Button>
                  </DialogClose>
                  <Button
                    className="bg-yellow-500 hover:bg-yellow-500 hover:scale-105"
                    onClick={handleAddRule}
                  >
                    Create Rule
                  </Button>
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
          <EscalationRulesCard escalationRules={rules} onToggle={toggleRuleStatus} onDelete={handleDeleteRule} />
          <RecentEscalationsCard recentEscalations={recentEscalations} />
        </div>
      </main>
    </div>
  );
}