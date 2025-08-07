import Sidebar from "@/components/ui/sidebar/support/sidebar";
import Header from "@/components/ui/header/support/header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex w-full min-h-screen bg-background text-foreground"> 
      <Sidebar />
      <div className="flex flex-col w-full">
        <Header />
        <main className="p-6 bg-background min-h-screen">{children}</main>
      </div>
    </div>
  );
}