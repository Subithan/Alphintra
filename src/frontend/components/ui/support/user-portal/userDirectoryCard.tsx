// components/ui/dashboard/UserDirectoryCard.tsx
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Eye, Edit, Mail, Phone, MapPin } from "lucide-react";

interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  location: string;
  status: string;
  tier: string;
  tickets: number;
  lastActive: string;
  joinDate: string;
}

interface UserDirectoryCardProps {
  users: User[];
  statusColors: Record<string, string>;
  tierColors: Record<string, string>;
}

export default function UserDirectoryCard({
  users,
  statusColors,
  tierColors,
}: UserDirectoryCardProps) {
  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle>User Directory</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {users.map((user) => (
            <div
              key={user.id}
              className="p-6 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Avatar className="h-12 w-12">
                    <AvatarImage
                      src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.name}`}
                    />
                    <AvatarFallback>
                      {user.name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")}
                    </AvatarFallback>
                  </Avatar>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-foreground">
                        {user.name}
                      </h3>
                      <Badge className={`text-xs ${statusColors[user.status]}`}>
                        {user.status}
                      </Badge>
                      <Badge className={`text-xs ${tierColors[user.tier]}`}>
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
                    <div className="text-muted-foreground">
                      Last active: {user.lastActive}
                    </div>
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
                          <DialogTitle>User Profile: {user.name}</DialogTitle>
                        </DialogHeader>
                        <div className="grid gap-6 py-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="text-sm font-medium text-muted-foreground">
                                User ID
                              </label>
                              <p className="text-sm">{user.id}</p>
                            </div>
                            <div>
                              <label className="text-sm font-medium text-muted-foreground">
                                Join Date
                              </label>
                              <p className="text-sm">{user.joinDate}</p>
                            </div>
                            <div>
                              <label className="text-sm font-medium text-muted-foreground">
                                Account Tier
                              </label>
                              <p className="text-sm capitalize">{user.tier}</p>
                            </div>
                            <div>
                              <label className="text-sm font-medium text-muted-foreground">
                                Total Tickets
                              </label>
                              <p className="text-sm">{user.tickets}</p>
                            </div>
                          </div>

                          <div>
                            <h4 className="font-medium mb-2">
                              Consent & Privacy
                            </h4>
                            <div className="space-y-2">
                              <div className="flex justify-between items-center">
                                <span className="text-sm">
                                  Marketing Communications
                                </span>
                                <Badge className="bg-green-100 text-green-800">
                                  Consented
                                </Badge>
                              </div>
                              <div className="flex justify-between items-center">
                                <span className="text-sm">Data Processing</span>
                                <Badge className="bg-green-100 text-green-800">
                                  Consented
                                </Badge>
                              </div>
                              <div className="flex justify-between items-center">
                                <span className="text-sm">Third-party Sharing</span>
                                <Badge className="bg-red-100 text-red-800">
                                  Declined
                                </Badge>
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
  );
}
