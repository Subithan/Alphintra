"use client";
import { Icon } from "@iconify/react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

const ThemeToggle = () => {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  const isDark = resolvedTheme === "dark";

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="relative p-2 hover:bg-gray-100 dark:hover:bg-[#262739] hover:text-yellow-500 rounded-full cursor-pointer"
    >
      <Icon
        icon={isDark ? "solar:sun-line-duotone" : "solar:moon-line-duotone"}
        height={20}
      />
    </button>
  );
};

export default ThemeToggle;
