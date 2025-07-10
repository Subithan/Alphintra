"use client";

import { useState, useEffect, useRef } from "react";
import LogoIcon from "@/components/ui/LogoIcon";
import Link from "next/link";
import { mainSidebarItems, footerSidebarItems } from "./sidebarData";
import SidebarItem from "./sidebarItem";
import { Icon } from "@iconify/react";
import { useTheme } from "next-themes";

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { resolvedTheme } = useTheme();
  const sidebarRef = useRef<HTMLElement>(null);

  // Mark component as mounted to avoid hydration issues
  useEffect(() => {
    setMounted(true);
  }, []);

  // Collapse sidebar automatically on small screens
  useEffect(() => {
    const handleResize = () => {
      setCollapsed(window.innerWidth < 768);
    };

    handleResize(); // initial check
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Log theme and sidebar background color after mount & theme change
  useEffect(() => {
    if (!mounted) return;

    console.log("Resolved theme:", resolvedTheme);

    if (sidebarRef.current) {
      const bgColor = window.getComputedStyle(sidebarRef.current).backgroundColor;
      console.log("Sidebar computed background color:", bgColor);
    }
  }, [resolvedTheme, mounted]);

  if (!mounted) return null; // Don't render on server or until mounted

  return (
    <aside
      ref={sidebarRef}
      className={`sticky top-0 left-0 h-screen ${
        collapsed ? "w-24" : "w-64"
      } p-4 flex flex-col justify-between transition-all duration-300 z-40 border-r border-[#a7adb7] dark:border-[#222c3e]`}
      style={{
        backgroundColor: "hsl(var(--background))",
        color: "hsl(var(--foreground))",
      }}
    >
      {/* Top Section */}
      <div>
        <div className="py-3 sm:py-4 lg:-mt-8 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="h-10 w-10 flex items-center justify-center p-2">
              <LogoIcon className="w-full h-full text-black dark:text-white" />
            </div>
            {!collapsed && (
              <span className="font-bold text-xl hidden sm:block text-black dark:text-white">
                ALPHINTRA
              </span>
            )}
          </Link>
        </div>

        <ul className="space-y-2 mt-4">
          {mainSidebarItems.map((item) => (
            <SidebarItem key={item.id} item={item} collapsed={collapsed} />
          ))}
        </ul>
      </div>

      {/* Bottom Section */}
      <div>
        <ul className="space-y-2 border-t border-[#a7adb7] dark:border-[#222c3e] pt-4 mb-2">
          {footerSidebarItems.map((item) => (
            <SidebarItem key={item.id} item={item} collapsed={collapsed} />
          ))}
        </ul>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className={`absolute top-[40px] -right-3 border rounded-sm w-6 h-6 flex items-center justify-center cursor-pointer group transition
          bg-white dark:bg-[#060819] border-[#a7adb7] dark:border-[#222c3e] text-[#a7adb7] dark:text-[#222c3e] hover:border-yellow-500`}
      >
        <Icon
          icon="solar:alt-arrow-left-linear"
          className={`group-hover:text-yellow-500 transition-transform duration-300 ${
            collapsed ? "rotate-180" : ""
          }`}
          width={16}
        />
      </button>
    </aside>
  );
};

export default Sidebar;
