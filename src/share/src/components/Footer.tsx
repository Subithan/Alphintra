import { Instagram, Facebook, Twitter, Youtube } from 'lucide-react';
import React from 'react'; // Import React for JSX in TypeScript

export const Footer = () => {
  return (
    <footer className='py-5 bg-black text-white/60 border-t border-white/20'>
      <div className="container">
        <div className='flex flex-col gap-4 sm:flex-row sm:justify-between'>
          <div className='text-center'>&copy; 2025 Alpintra, Inc. All rights reserved</div>
          <ul className='flex justify-center gap-2.5'>
            <li><Instagram /></li>
            <li><Facebook /></li>
            <li><Twitter /></li>
            <li><Youtube /></li>
          </ul>
        </div>
      </div>
    </footer>
  )
};