"use client";
import { useState, useEffect } from "react";
import { useTheme } from 'next-themes';
import LogoIcon from "@/components/ui/LogoIcon";
import Link from "next/link";
import { mainSidebarItems, footerSidebarItems } from "./sidebarData";
import SidebarItem from "./sidebarItem";
import { Icon } from "@iconify/react";

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { theme, systemTheme } = useTheme();

  // Flag component as mounted to avoid hydration mismatch
  useEffect(() => setMounted(true), []);

  // Handle responsive collapse
  useEffect(() => {
    const handleResize = () => setCollapsed(window.innerWidth < 768);
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (!mounted) return null;
  const currentTheme = theme === 'system' ? systemTheme : theme;

  return (
    <aside
      className={`sticky top-0 left-0 h-screen ${
        collapsed ? "w-24" : "w-64"
      } ${currentTheme === 'dark' ? 'bg-[#0a0a1a] text-white border-yellow-500/20' : 'bg-white text-gray-900 border-gray-300'} border-r p-4 flex flex-col justify-between transition-all duration-300 z-40 shadow-lg`}
    >
      {/* Top Section */}
      <div>
        <div className="py-3 sm:py-4 lg:-mt-8 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="h-10 w-10 bg-yellow-400 rounded-full flex items-center justify-center p-2">
              <LogoIcon className="text-black w-full h-full" />
            </div>
            {!collapsed && (
              <span className={`${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} font-bold text-xl hidden sm:block`}>ALPHINTRA</span>
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
        <ul className={`space-y-2 border-t ${currentTheme === 'dark' ? 'border-yellow-500/20' : 'border-gray-300'} pt-4 mb-2`}>
          {footerSidebarItems.map((item) => (
            <SidebarItem key={item.id} item={item} collapsed={collapsed} />
          ))}
        </ul>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className={`absolute top-[40px] -right-3 ${currentTheme === 'dark' ? 'bg-[#0a0a1a] border-yellow-500/20' : 'bg-white border-gray-300'} hover:border-yellow-500 border rounded-md w-6 h-6 flex items-center justify-center cursor-pointer group transition shadow-lg`}
      >
        <Icon
          icon="solar:alt-arrow-left-linear"
          className={`${currentTheme === 'dark' ? 'text-white' : 'text-gray-600'} group-hover:text-yellow-500 transition-transform duration-300 ${
            collapsed ? "rotate-180" : ""
          }`}
          width={16}
        />
      </button>
    </aside>
  );
};

export default Sidebar;