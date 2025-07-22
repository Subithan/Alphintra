
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Store, TrendingUp, DollarSign, Package } from "lucide-react"

export default function Marketplace() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <main className="flex-1 p-6 space-y-6">
        <div className="grid gap-4 md:grid-cols-4">
          <Card className="shadow-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Store className="h-5 w-5 text-blue-600" />
                <div>
                  <div className="text-2xl font-bold">45</div>
                  <p className="text-sm text-muted-foreground">Active Models</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Package className="h-5 w-5 text-green-600" />
                <div>
                  <div className="text-2xl font-bold">12</div>
                  <p className="text-sm text-muted-foreground">Vendors</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-yellow-600" />
                <div>
                  <div className="text-2xl font-bold">$24.8K</div>
                  <p className="text-sm text-muted-foreground">Monthly Revenue</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-purple-600" />
                <div>
                  <div className="text-2xl font-bold">+15%</div>
                  <p className="text-sm text-muted-foreground">Growth Rate</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Marketplace Models Panel</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">Comprehensive marketplace model management and vendor integration tools.</p>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}