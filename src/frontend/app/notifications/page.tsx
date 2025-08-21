"use client";

import { useState } from "react";

const NotificationsPage = () => {
  // You can move your notifications data here or fetch from an API
  const notifications = [
    { id: 1, title: "Launch Admin", message: "Just see the my new admin!", time: "9:30 AM", read: false },
    { id: 2, title: "Event Today", message: "Just a reminder that you have...", time: "9:15 AM", read: false },
    { id: 3, title: "Settings", message: "You can customize this template...", time: "4:36 PM", read: true },
    // Add more notifications...
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        All Notifications
      </h1>
      
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-800">
        {notifications.map((notification) => (
          <div
            key={notification.id}
            className={`flex items-center px-6 py-4 border-b border-gray-200 dark:border-gray-800 last:border-b-0 ${
              !notification.read ? 'bg-yellow-50 dark:bg-yellow-900/10' : ''
            }`}
          >
            <div className="flex-1">
              <div className="text-lg font-medium text-gray-900 dark:text-white">
                {notification.title}
              </div>
              <div className="text-gray-600 dark:text-gray-400 mt-1">
                {notification.message}
              </div>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {notification.time}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NotificationsPage;
