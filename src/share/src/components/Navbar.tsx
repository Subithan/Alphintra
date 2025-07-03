"use client";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import LogoIcon from "../app/assets/logo/logoIcon"; // This might need to be converted to .tsx as well
import LogoText from "../app/assets/logo/logoText"; // This might need to be converted to .tsx as well
import React from 'react'; // Import React for JSX in TypeScript

export const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false); // Explicitly type useState

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  const handleNavClick = () => {
    setIsMenuOpen(false);
  };

  interface NavItem {
    label: string;
    href: string;
  }

  const navItems: NavItem[] = [
    { label: "About", href: "#About" },
    { label: "Features", href: "#Features" },
    { label: "FAQ", href: "#FAQ" },
    { label: "Updates", href: "#Updates" },
  ];

  return (
    <div className="bg-black">
      <div className="px-4">
        <div className="py-2 lg:-mt-8 flex items-center justify-between">
          <Link href="/" aria-label="Homepage" className="flex items-center gap-1">
            <LogoIcon className="h-12 w-12 text-white" />
            <LogoText className="h-28 w-auto text-white hidden sm:block" />
          </Link>
          <div
            className="text-white border border-white/30 h-10 w-10 inline-flex justify-center items-center rounded-lg lg:hidden cursor-pointer"
            onClick={toggleMenu}
          >
            {isMenuOpen ? <X /> : <Menu />}
          </div>
          <nav className="hidden lg:flex gap-14 items-center">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="text-white/60 hover:text-yellow-400 transition"
                onClick={handleNavClick}
                scroll={true}
              >
                {item.label}
              </Link>
            ))}
            <div className="flex gap-2">
              <button
                className="border-yellow-400 border-2 text-yellow-400 py-2 px-4 rounded-lg hover:scale-105 transition"
              >
                Log In
              </button>
              <button
                className="bg-yellow-400 text-[#312e81] py-2 px-4 rounded-lg border-2 border-yellow-400 hover:scale-105 transition"
              >
                Get for Free
              </button>
            </div>
          </nav>
        </div>
        {/* Mobile Menu */}
        {isMenuOpen && (
          <nav className="flex flex-col gap-4 pb-4 lg:hidden">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="text-white/60 hover:text-yellow-400 transition"
                onClick={handleNavClick}
                scroll={true}
              >
                {item.label}
              </Link>
            ))}
            <button
              className="border-yellow-400 border-2 text-yellow-400 py-2 px-4 rounded-lg hover:bg-white/10 transition"
              onClick={handleNavClick}
            >
              Log In
            </button>
            <button
              className="bg-yellow-400 text-[#312e81] py-2 px-4 rounded-lg border-2 border-yellow-400 hover:bg-gray-200 transition"
              onClick={handleNavClick}
            >
              Get for Free
            </button>
          </nav>
        )}
      </div>
    </div>
  );
};