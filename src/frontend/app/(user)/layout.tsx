
"use client"
import Sidebar from "@/components/ui/sidebar/sidebar";
import Header from "@/components/ui/header/header";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  // Prevent SSR mismatch
  if (!mounted) return null;

  return (
    <div className="flex w-full min-h-screen bg-background text-foreground transition-colors duration-300">
      <Sidebar />
      <div className="flex flex-col w-full">
        <Header />
        <main className="p-6 bg-background text-foreground min-h-screen overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
