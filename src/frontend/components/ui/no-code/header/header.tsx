"use client";
import { useState, useEffect } from "react";
import Notification from "./notification";
import ThemeToggle from "./themeToggle"; 
import SearchBar from "./searchBar";    
import Profile from "./profile"; 

const Header = () => {
  return (
    <header
      className={`transition ${"bg-transparent"}`}
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