"use client";

import { useState, useEffect } from "react";
import { useTheme } from 'next-themes';

const SearchBar = () => {
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) return null;
  const currentTheme = theme === 'system' ? systemTheme : theme;

  return (
    <input
      type="text"
      placeholder="Search..."
      className={`px-6 py-2 rounded-full text-sm font-medium flex items-center space-x-2 transition duration-200 outline-none focus:outline-none ${currentTheme === 'dark' ? 'bg-[#141426] text-white border border-yellow-500/20' : 'bg-gray-100 text-gray-900 border border-gray-200'}`}
    />
  );
};

export default SearchBar;