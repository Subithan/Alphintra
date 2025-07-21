"use client";
import { useState, useRef, useEffect } from "react";
import { useTheme } from 'next-themes';
import Link from "next/link";
import Image from "next/image";
import { Icon } from "@iconify/react";

const Profile = () => {
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => setMounted(true), []);
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!mounted) return null;
  const currentTheme = theme === 'system' ? systemTheme : theme;

  

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Avatar Button */}
      <button
        onClick={() => setOpen(!open)}
        className="rounded-full cursor-pointer focus:outline-none"
      >
        <Image
          src="/images/profile/user-1.jpg"
          alt="Profile"
          width={36}
          height={36}
          className="rounded-full"
        />
      </button>

      {/* Dropdown Menu */}
      {open && (
        <div className={`absolute right-0 mt-2 w-48 rounded-md shadow-lg z-50 border transition-all ${currentTheme === 'dark' ? 'bg-[#0a0a1a] border-yellow-500/20' : 'bg-gray-50 border-gray-200'}`}>
          <Link
            href="/profile"
            className={`flex items-center gap-2 px-4 py-2 text-sm transition-colors ${currentTheme === 'dark' ? 'text-white hover:bg-[#141426]' : 'text-gray-900 hover:bg-gray-100'}`}
            onClick={() => setOpen(false)}
          >
            <Icon icon="solar:user-circle-outline" width={20} />
            My Profile
          </Link>

          <Link
            href="/settings"
            className={`flex items-center gap-2 px-4 py-2 text-sm transition-colors ${currentTheme === 'dark' ? 'text-white hover:bg-[#141426]' : 'text-gray-900 hover:bg-gray-100'}`}
            onClick={() => setOpen(false)}
          >
            <Icon icon="solar:settings-outline" width={20} />
            Settings
          </Link>

          <div className=" dark:border-gray-700 my-1" />

          <Link
            href="/auth/login"
            className={`block w-full text-left px-4 py-2 text-sm transition-colors ${currentTheme === 'dark' ? 'text-white hover:bg-[#141426] border-t border-yellow-500/20' : 'text-gray-900 hover:bg-gray-100 border-t border-gray-200'}` }
            onClick={() => setOpen(false)}
          >
            Logout
          </Link>
        </div>
      )}
    </div>
  );
};

export default Profile;