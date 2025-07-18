
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DialogClose } from "@radix-ui/react-dialog";
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Plus, Eye, Edit, Shield, User, MapPin, Calendar, Mail, Phone, X } from "lucide-react"
import { SearchBar } from "@/components/ui/searchBar";

const users = [
  {
    id: "USR001",
    name: "Alex Johnson",
    email: "alex.johnson@email.com",
    phone: "+1 (555) 123-4567",
    location: "New York, NY",
    joinDate: "Jan 15, 2024",
    status: "active",
    tier: "premium",
    tickets: 5,
    lastActive: "2 hours ago"
  },
  {
    id: "USR002", 
    name: "Maria Garcia",
    email: "maria.garcia@email.com",
    phone: "+1 (555) 987-6543",
    location: "Los Angeles, CA",
    joinDate: "Mar 8, 2024",
    status: "active",
    tier: "standard",
    tickets: 12,
    lastActive: "1 day ago"
  },
  {
    id: "USR003",
    name: "David Chen",
    email: "david.chen@email.com", 
    phone: "+1 (555) 456-7890",
    location: "San Francisco, CA",
    joinDate: "Feb 22, 2024",
    status: "pending",
    tier: "basic",
    tickets: 3,
    lastActive: "3 days ago"
  }
]

const statusColors = {
  active: "bg-green-100 text-green-800",
  pending: "bg-yellow-100 text-yellow-800",
  inactive: "bg-gray-100 text-gray-800"
}

const tierColors = {
  premium: "bg-purple-100 text-purple-800",
  standard: "bg-blue-100 text-blue-800", 
  basic: "bg-gray-100 text-gray-800"
}

export default function Users() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <main className="flex-1 p-6 pt-0 space-y-6">
        <div className="p-4 flex justify-end items-center gap-4 flex-wrap">
          <SearchBar placeholder="Search users..." className="w-full sm:w-72" />
          <Button className="bg-yellow-500 hover:bg-yellow-500 hover:scale-105 gap-2 text-sm whitespace-nowrap">
            <Plus className="h-4 w-4" /> Add User
          </Button>
        </div>
        {/* User Snapshot Dashboard */}
        <div className="grid gap-6 md:grid-cols-3">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="text-lg">Total Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">12,847</div>
              <p className="text-sm text-muted-foreground">+5.2% this month</p>
            </CardContent>
          </Card>

          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="text-lg">Active Users</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">9,234</div>
              <p className="text-sm text-muted-foreground">72% of total users</p>
            </CardContent>
          </Card>

          <Card className="shadow-card">
            <CardHeader>
              <CardTitle className="text-lg">New This Week</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">287</div>
              <p className="text-sm text-muted-foreground">+12% vs last week</p>
            </CardContent>
          </Card>
        </div>

        {/* User List */}
        <Card className="shadow-card">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>User Directory</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              {users.map((user) => (
                <div key={user.id} className="p-6 hover:bg-muted/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Avatar className="h-12 w-12">
                        <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.name}`} />
                        <AvatarFallback>{user.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                      </Avatar>
                      
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-foreground">{user.name}</h3>
                          <Badge className={`text-xs ${statusColors[user.status as keyof typeof statusColors]}`}>
                            {user.status}
                          </Badge>
                          <Badge className={`text-xs ${tierColors[user.tier as keyof typeof tierColors]}`}>
                            {user.tier}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            {user.email}
                          </div>
                          <div className="flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {user.phone}
                          </div>
                          <div className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" />
                            {user.location}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right text-sm">
                        <div className="font-medium">{user.tickets} tickets</div>
                        <div className="text-muted-foreground">Last active: {user.lastActive}</div>
                      </div>
                      
                      <div className="flex gap-2">
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-2xl">
                            <DialogHeader>
                              <DialogTitle className="text-black dark:text-white">User Profile: {user.name}</DialogTitle>
                            </DialogHeader>
                              <DialogClose className="absolute right-4 top-4 rounded-md p-1 transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring">
                                <X className="h-4 w-4 text-black dark:text-white" />
                                <span className="sr-only">Close</span>
                            </DialogClose>
                            <div className="grid gap-6 py-4">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <label className="text-sm font-medium text-muted-foreground">User ID</label>
                                  <p className="text-sm text-black dark:text-white">{user.id}</p>
                                </div>
                                <div>
                                  <label className="text-sm font-medium text-muted-foreground">Join Date</label>
                                  <p className="text-sm text-black dark:text-white">{user.joinDate}</p>
                                </div>
                                <div>
                                  <label className="text-sm font-medium text-muted-foreground">Account Tier</label>
                                  <p className="text-sm capitalize text-black dark:text-white">{user.tier}</p>
                                </div>
                                <div>
                                  <label className="text-sm font-medium text-muted-foreground">Total Tickets</label>
                                  <p className="text-sm text-black dark:text-white">{user.tickets}</p>
                                </div>
                              </div>
                              
                              <div>
                                <h4 className="font-medium mb-2 text-black dark:text-white">Consent & Privacy</h4>
                                <div className="space-y-2 text-black dark:text-white">
                                  <div className="flex justify-between items-center ">
                                    <span className="text-sm ">Marketing Communications</span>
                                    <Badge className="bg-green-100 text-green-800">Consented</Badge>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm">Data Processing</span>
                                    <Badge className="bg-green-100 text-green-800">Consented</Badge>
                                  </div>
                                  <div className="flex justify-between items-center">
                                    <span className="text-sm">Third-party Sharing</span>
                                    <Badge className="bg-red-100 text-red-800">Declined</Badge>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                        
                        <Button variant="ghost" size="sm">
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}