// NewsCard.tsx
import React from 'react';

import { Megaphone, MoreHorizontal } from 'lucide-react';

interface NewsCardProps {
  title: string;
  source: string;
  time: string;
}

export default function NewsCard({ title, source, time }: NewsCardProps) {
  return (
      <div className="border border-[#262739] p-4 rounded-lg shadow-lg mb-4">
        <div className="flex items-center">
          <div className="text-white rounded-full w-6 h-6 flex items-center justify-center mr-2">
            <Megaphone className="w-6 h-6 text-yellow-500 mr-2" />
          </div>
          <div>
            <h3 className="text-white text-2xs font-bold">{title}</h3>
            <p className="text-gray-400 text-sm">{source} · {time}</p>
          </div>
        </div>
      </div>
  );
}