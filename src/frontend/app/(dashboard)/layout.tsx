import Sidebar from "@/components/ui/sidebar/sidebar";
import Header from "@/components/ui/header/header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex w-full min-h-screen bg-[#060819]">
      <Sidebar />
      <div className="flex flex-col w-full">
        <Header />
        <main className="p-6 bg-[#060819] min-h-screen">{children}</main>
      </div>
    </div>
  );
}