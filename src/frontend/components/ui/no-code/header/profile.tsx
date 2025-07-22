"use client";
import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { Icon } from "@iconify/react";

const Profile = () => {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
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
        <div className="absolute right-0 mt-2 w-48 bg-gray-900 border-[#262739] dark:bg-gray-800 rounded-md shadow-lg z-50">
          <Link
            href="/profile"
            className="flex items-center gap-2 px-4 py-2 hover:bg-[#262739] dark:hover:bg-gray-700 text-sm text-white dark:text-gray-200"
            onClick={() => setOpen(false)}
          >
            <Icon icon="solar:user-circle-outline" width={20} />
            My Profile
          </Link>

          <Link
            href="/settings"
            className="flex items-center gap-2 px-4 py-2 hover:bg-[#262739] dark:hover:bg-gray-700 text-sm text-white dark:text-gray-200"
            onClick={() => setOpen(false)}
          >
            <Icon icon="solar:settings-outline" width={20} />
            Settings
          </Link>

          <div className=" dark:border-gray-700 my-1" />

          <Link
            href="/auth/login"
            className=" border-t border-[#262739] block w-full text-left px-4 py-2 hover:bg-[#262739] dark:hover:bg-gray-700 text-sm text-white"
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