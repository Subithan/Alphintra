"use client";

import { Icon } from "@iconify/react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

const ThemeToggle = () => {
  const { theme, setTheme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Ensure component is mounted before accessing theme to avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  // Resolve the currently active theme (light / dark / system)
  const currentTheme = theme === "system" ? systemTheme : theme;
  const isDark = currentTheme === "dark";

  const toggleTheme = () => {
    setTheme(isDark ? "light" : "dark");
  };

  return (
    <button
      onClick={toggleTheme}
      className={`p-2 rounded-full transition-all ${isDark ? "hover:bg-[#141426] hover:text-yellow-500" : "hover:bg-gray-100 hover:text-yellow-500"}`}
      aria-label="Toggle theme"
    >
      <Icon
        icon={isDark ? "solar:moon-line-duotone" : "solar:sun-line-duotone"}
        height={20}
      />
    </button>
  );
};

export default ThemeToggle;