"use client";

import { useState, useEffect, useRef } from "react";
import { useTheme } from "next-themes";
import { Icon } from "@iconify/react";
import Link from "next/link";

const Notification = () => {
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => setMounted(true), []);
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
  if (!mounted) return null;
  const currentTheme = theme === "system" ? systemTheme : theme;

  const notifications = [
    { id: 1, title: "Launch Admin", message: "Just see the my new admin!", time: "9:30 AM" },
    { id: 2, title: "Event Today", message: "Just a reminder that you have...", time: "9:15 AM" },
    { id: 3, title: "Settings", message: "You can customize this template...", time: "4:36 PM" },
    { id: 4, title: "Launch Admin", message: "Just see the my new admin!", time: "9:30 AM" },
    { id: 5, title: "Event Today", message: "Just a reminder that you have...", time: "9:15 AM" },
    { id: 6, title: "Event Today", message: "Just a reminder that you have...", time: "9:15 AM" },
  ];

  

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Notifications"
        className={`relative p-2 rounded-full cursor-pointer transition-all ${currentTheme === "dark" ? "hover:bg-gray-700" : "hover:bg-gray-100"} hover:text-yellow-500`} 
      >
        <Icon icon="solar:bell-linear" width={20} />
        <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-yellow-500"></span>
      </button>

      {isOpen && (
        <div className={`absolute right-0 mt-2 w-72 rounded-lg shadow-lg z-50 border transition-all ${currentTheme === "dark" ? "bg-gray-800 border-gray-700" : "bg-gray-50 border-gray-200"}`} >
          <div className={`p-4 text-lg font-semibold flex justify-between items-center transition-all ${currentTheme === "dark" ? "text-white border-b border-gray-700" : "text-gray-900 border-b border-gray-200"}`} >
            Notifications
            <span className={`px-2 py-1 rounded-full text-xs ${currentTheme === "dark" ? "bg-yellow-500 text-black" : "bg-yellow-500 text-white"}`}>
            
              {notifications.length} new
            </span>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`flex items-center px-4 py-2 transition-colors ${currentTheme === "dark" ? "text-white hover:bg-[#141426]" : "text-gray-900 hover:bg-gray-100"}`} 
              >
               
                <div className="flex-1">
                  <div className="text-sm font-medium">{notification.title}</div>
                  <div className="text-xs text-gray-400">{notification.message}</div>
                </div>
                <div className="text-xs text-gray-500">{notification.time}</div>
              </div>
            ))}
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className={`w-full px-4 py-2 text-sm font-medium rounded-b-lg transition-all ${currentTheme === "dark" ? "bg-[#0a0a1a] text-yellow-500 hover:bg-[#141426]" : "bg-gray-50 text-yellow-500 hover:bg-gray-100"}`} 
          >
            See All Notifications
          </button>
        </div>
      )}
    </div>
  );
};

export default Notification;