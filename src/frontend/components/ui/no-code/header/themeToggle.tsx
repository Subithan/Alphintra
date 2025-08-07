"use client";
import { useEffect, useState } from "react";
import { Icon } from "@iconify/react";

const ThemeToggle = () => {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.toggle("dark", darkMode);
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  useEffect(() => {
    const saved = localStorage.getItem("theme");
    setDarkMode(saved === "dark");
  }, []);

  return (
    <button
      onClick={() => setDarkMode(!darkMode)}
      className="p-2 rounded-full hover:bg-[#262739] hover:text-yellow-500 dark:hover:bg-gray-800"
    >
      <Icon
        icon={darkMode ? "solar:moon-line-duotone" : "solar:sun-line-duotone"}
        height={20}
      />
    </button>
  );
};

export default ThemeToggle;