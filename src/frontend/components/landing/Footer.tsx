import { Instagram, Facebook, Twitter, Youtube } from 'lucide-react';
import React from 'react';
import LogoIcon from "@/components/ui/LogoIcon";

export const Footer = () => {
  return (
    <footer className='py-8 bg-black text-white/60 border-t border-white/20'>
      <div className="container mx-auto px-4">
        <div className='flex flex-col gap-6 sm:flex-row sm:justify-between items-center'>
          <div className='text-center sm:text-left'>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 bg-yellow-400 rounded-full flex items-center justify-center p-1">
                <LogoIcon className="text-black w-full h-full" />
              </div>
              <span className="text-white font-bold">ALPHINTRA</span>
            </div>
            <p>&copy; 2025 Alphintra, Inc. All rights reserved</p>
          </div>
          <ul className='flex justify-center gap-4'>
            <li className="hover:text-yellow-400 transition-colors cursor-pointer">
              <Instagram className="w-5 h-5" />
            </li>
            <li className="hover:text-yellow-400 transition-colors cursor-pointer">
              <Facebook className="w-5 h-5" />
            </li>
            <li className="hover:text-yellow-400 transition-colors cursor-pointer">
              <Twitter className="w-5 h-5" />
            </li>
            <li className="hover:text-yellow-400 transition-colors cursor-pointer">
              <Youtube className="w-5 h-5" />
            </li>
          </ul>
        </div>
      </div>
    </footer>
  );
};