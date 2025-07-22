// components/ui/support/escaltion/escalationRulesCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Settings } from "lucide-react"

export type EscalationRule = {
  id: string
  name: string
  description: string
  trigger: string
  condition: string
  action: string
  status: "active" | "inactive"
  triggered: number
}

type Props = {
  escalationRules: EscalationRule[]
  onToggle: (id: string) => void
}

export function EscalationRulesCard({ escalationRules, onToggle }: Props) {
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
            <Switch
            checked={rule.status === "active"}
            onCheckedChange={() => onToggle(rule.id)}
            className={`${
                rule.status === "active"
                ? "bg-yellow-500"  // active color
                : "bg-gray-300"   // inactive color
            }`}
            />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
