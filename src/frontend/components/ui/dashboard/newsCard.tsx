'use client';

import React, { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
import { Megaphone, MoreHorizontal } from 'lucide-react';

interface NewsCardProps {
  title: string;
  source: string;
  time: string;
}

export default function NewsCard({ title, source, time }: NewsCardProps) {
  const { theme, systemTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  if (!mounted) return null;
  const currentTheme = theme === 'system' ? systemTheme : theme;

  return (
      <div className={`p-3 rounded-lg ${currentTheme === 'dark' ? 'bg-[#0a0a1a] border border-yellow-500/20 hover:bg-[#141426]' : 'bg-gray-50 border border-gray-200 hover:bg-gray-100'} transition-all cursor-pointer`}>
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-yellow-500/10 flex-shrink-0">
            <Megaphone className="w-4 h-4 text-yellow-500" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className={`${currentTheme === 'dark' ? 'text-white' : 'text-gray-900'} text-sm font-semibold leading-tight mb-1 line-clamp-2`}>
              {title}
            </h3>
            <p className={`${currentTheme === 'dark' ? 'text-slate-400' : 'text-gray-600'} text-xs`}>
              {source} · {time}
            </p>
          </div>
        </div>
      </div>
  );
}