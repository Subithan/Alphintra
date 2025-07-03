"use client";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import React from 'react';
import LogoIcon from "@/components/ui/LogoIcon";

export const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  const handleNavClick = () => {
    setIsMenuOpen(false);
  };

  interface NavItem {
    label: string;
    href: string;
  }

  const navItems: NavItem[] = [
    { label: "About", href: "#about" },
    { label: "Features", href: "#features" },
    { label: "FAQ", href: "#faq" },
    { label: "Updates", href: "#updates" },
  ];

  return (
    <div className="bg-black/95 backdrop-blur-sm fixed w-full top-0 z-50 border-b border-white/10">
      <div className="px-4">
        <div className="py-4 flex items-center justify-between">
          <Link href="/" aria-label="Homepage" className="flex items-center gap-2">
            <div className="h-12 w-12 bg-yellow-400 rounded-full flex items-center justify-center p-2">
              <LogoIcon className="text-black w-full h-full" />
            </div>
            <span className="text-white font-bold text-xl hidden sm:block">ALPHINTRA</span>
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
              <Link
                href="/auth"
                className="border-yellow-400 border-2 text-yellow-400 py-2 px-4 rounded-lg hover:scale-105 transition inline-block"
              >
                Log In
              </Link>
              <Link
                href="/auth"
                className="bg-yellow-400 text-[#312e81] py-2 px-4 rounded-lg border-2 border-yellow-400 hover:scale-105 transition inline-block"
              >
                Get for Free
              </Link>
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
            <Link
              href="/auth"
              className="border-yellow-400 border-2 text-yellow-400 py-2 px-4 rounded-lg hover:bg-white/10 transition inline-block text-center"
              onClick={handleNavClick}
            >
              Log In
            </Link>
            <Link
              href="/auth"
              className="bg-yellow-400 text-[#312e81] py-2 px-4 rounded-lg border-2 border-yellow-400 hover:bg-gray-200 transition inline-block text-center"
              onClick={handleNavClick}
            >
              Get for Free
            </Link>
          </nav>
        )}
      </div>
    </div>
  );
};