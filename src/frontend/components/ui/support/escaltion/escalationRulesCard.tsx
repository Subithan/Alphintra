import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from "@/components/ui/dialog";
import { Settings, Trash2, X } from "lucide-react";

export type EscalationRule = {
  id: string;
  name: string;
  description: string;
  trigger: string;
  condition: string;
  action: string;
  status: "active" | "inactive";
  triggered: number;
};

type Props = {
  escalationRules: EscalationRule[];
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
};

export function EscalationRulesCard({ escalationRules, onToggle, onDelete }: Props) {
  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Escalation Rules
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {escalationRules.map((rule) => (
          <div key={rule.id} className="p-4 border border-border rounded-lg">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-semibold text-foreground">{rule.name}</h4>
                </div>
                <p className="text-sm text-muted-foreground mb-2">{rule.description}</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div><span className="font-medium">Trigger:</span> {rule.trigger}</div>
                  <div><span className="font-medium">Condition:</span> {rule.condition}</div>
                  <div><span className="font-medium">Action:</span> {rule.action}</div>
                  <div><span className="font-medium">Triggered:</span> {rule.triggered} times</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={rule.status === "active"}
                  onCheckedChange={() => onToggle(rule.id)}
                  className={`${rule.status === "active" ? "bg-yellow-500" : "bg-gray-300"}`}
                />
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-md">
                    <DialogHeader>
                      <DialogTitle className="text-black dark:text-white">Delete Rule: {rule.id}</DialogTitle>
                    </DialogHeader>
                    <DialogClose
                      className="absolute right-4 top-4 rounded-md p-1 transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                      <X className="h-4 w-4 text-black dark:text-white" />
                      <span className="sr-only">Close</span>
                    </DialogClose>
                    <div className="space-y-4">
                      <p className="text-sm text-muted-foreground">
                        Are you sure you want to delete rule {rule.id}? This action cannot be undone.
                      </p>
                      <div className="flex justify-end gap-2">
                        <DialogClose asChild>
                          <Button variant="outline">Cancel</Button>
                        </DialogClose>
                        <DialogClose asChild>
                          <Button
                            className="bg-yellow-500 hover:bg-yellow-500 hover:scale-105"
                            onClick={() => onDelete(rule.id)}
                          >
                            Delete
                          </Button>
                        </DialogClose>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}