"use client";
import { useState, useEffect } from "react";
import Notification from "./notification";
import ThemeToggle from "./themeToggle"; 
import SearchBar from "./searchBar";    
import Profile from "./profile"; 

const Header = () => {
  return (
    <header
      className={`px-4 py-3 bg-gray-50 border-b border-gray-200 dark:bg-[#0a0a1a] dark:border-yellow-500/20 transition-all`}
    >
      <div className="flex justify-between items-center px-4 py-3">
        {/* Left side (can add logo or leave empty) */}
        <div></div>

        {/* Right Section */}
        <div className="flex items-center gap-4">
          <SearchBar /> 
          <Notification />
          <ThemeToggle />
          <Profile />
        </div>
      </div>
    </header>
  );
};

export default Header;