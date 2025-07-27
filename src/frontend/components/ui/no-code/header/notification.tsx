"use client";

import { useState, useEffect, useRef } from "react";
import { Icon } from "@iconify/react";
import Link from "next/link";
import { theme } from "../theme";

const Notification = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const notifications = [
    { id: 1, title: "Launch Admin", message: "Just see the my new admin!", time: "9:30 AM" },
    { id: 2, title: "Event Today", message: "Just a reminder that you have...", time: "9:15 AM" },
    { id: 3, title: "Settings", message: "You can customize this template...", time: "4:36 PM" },
    { id: 4, title: "Launch Admin", message: "Just see the my new admin!", time: "9:30 AM" },
    { id: 5, title: "Event Today", message: "Just a reminder that you have...", time: "9:15 AM" },
    { id: 6, title: "Event Today", message: "Just a reminder that you have...", time: "9:15 AM" },
  ];

  // Close dropdown if clicked outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Notifications"
        className="relative p-2 hover:bg-gray-700 hover:text-yellow-500 rounded-full cursor-pointer"
        style={{ backgroundColor: theme.colors.dark.cardBorder }}
      >
        <Icon icon="solar:bell-linear" width={20} />
        <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-yellow-500"></span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-gray-900 rounded-lg shadow-lg z-50 border border-gray-800">
          <div className="p-4 text-white text-lg font-semibold border-b border-gray-800 flex justify-between items-center">
            Notifications
            <span className="px-2 py-1 bg-yellow-500 text-white text-xs rounded-full">
              {notifications.length} new
            </span>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className="flex items-center px-4 py-2 text-white transition-colors"
                style={{ backgroundColor: theme.colors.dark.cardBorder }}
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
            className="w-full px-4 py-2 text-yellow-500 rounded-b-lg text-sm font-medium"
            style={{ backgroundColor: theme.colors.dark.cardBorder }}
          >
            See All Notifications
          </button>
        </div>
      )}
    </div>
  );
};

export default Notification;