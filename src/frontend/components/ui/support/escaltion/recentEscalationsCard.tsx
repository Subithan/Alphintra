// components/escalation/RecentEscalationsCard.tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface Escalation {
  ticket: string
  customer: string
  status: "pending" | "resolved"
  rule: string
  escalatedTo: string
  time: string
}

interface Props {
  recentEscalations: Escalation[]
}

export function RecentEscalationsCard({ recentEscalations }: Props) {
  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle>Recent Escalations</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {recentEscalations.map((escalation, index) => (
          <div key={index} className="p-4 border border-border rounded-lg">
            <div className="flex justify-between items-start mb-2">
              <div>
                <div className="font-semibold text-foreground">{escalation.ticket}</div>
                <div className="text-sm text-muted-foreground">{escalation.customer}</div>
              </div>
              <Badge className={`text-xs ${escalation.status === 'resolved' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                {escalation.status}
              </Badge>
            </div>
            <div className="text-sm space-y-1">
              <div><span className="font-medium">Rule:</span> {escalation.rule}</div>
              <div><span className="font-medium">Escalated to:</span> {escalation.escalatedTo}</div>
              <div className="text-muted-foreground">{escalation.time}</div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
