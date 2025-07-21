'use client';

import Sidebar from "@/components/ui/sidebar/sidebar";
import Header from "@/components/ui/header/header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {

  return (
    <div className="flex w-full min-h-screen bg-gray-50 dark:bg-[#0a0a1a]">
      <Sidebar />
      <div className="flex flex-col w-full">
        <Header />
        <main className="p-6 min-h-screen bg-gray-50 dark:bg-[#0a0a1a]">
          {children}
        </main>
      </div>
    </div>
  );
}