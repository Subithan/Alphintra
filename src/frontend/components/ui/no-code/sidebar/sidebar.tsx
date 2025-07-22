"use client";
import { useState, useEffect } from "react";
import LogoIcon from "@/components/ui/LogoIcon";
import Link from "next/link";
import { mainSidebarItems, footerSidebarItems } from "./sidebarData";
import SidebarItem from "./sidebarItem";
import { Icon } from "@iconify/react";

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);

  // Collapse sidebar automatically on small screens
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setCollapsed(true);
      } else {
        setCollapsed(false);
      }
    };

    // Initial check
    handleResize();

    // Listen for resize events
    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <aside
      className={`sticky top-0 left-0 h-screen ${
        collapsed ? "w-24" : "w-64"
      } bg-[#060819] text-white border-r border-[#262739] p-4 flex flex-col justify-between transition-all duration-300 z-40`}
    >
      {/* Top Section */}
      <div>
        <div className="py-3 sm:py-4 lg:-mt-8 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="h-10 w-10 bg-yellow-400 rounded-full flex items-center justify-center p-2">
              <LogoIcon className="text-black w-full h-full" />
            </div>
            {!collapsed && (
              <span className="text-white font-bold text-xl hidden sm:block">ALPHINTRA</span>
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
        <ul className="space-y-2 border-t border-[#262739] pt-4 mb-2">
          {footerSidebarItems.map((item) => (
            <SidebarItem key={item.id} item={item} collapsed={collapsed} />
          ))}
        </ul>
      </div>

      {/* Collapse Toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute top-[40px] -right-3 bg-[#060819] hover:border-yellow-500 border rounded-sm border-[#262739] w-6 h-6 flex items-center justify-center cursor-pointer group transition"
      >
        <Icon
          icon="solar:alt-arrow-left-linear"
          className={`text-white group-hover:text-yellow-500 transition-transform duration-300 ${
            collapsed ? "rotate-180" : ""
          }`}
          width={16}
        />
      </button>
    </aside>
  );
};

export default Sidebar;