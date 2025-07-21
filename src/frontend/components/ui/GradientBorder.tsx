'use client';

import React from 'react';
import { useTheme } from 'next-themes';

interface GradientBorderProps {
  children: React.ReactNode;
  gradientAngle: '45deg' | '135deg' | '225deg' | '275deg' | '315deg';
  backgroundColor?: string;
  className?: string;
}

const GradientBorder: React.FC<GradientBorderProps> = ({
  children,
  gradientAngle,
  backgroundColor,
  className = '',
}) => {
  const { theme } = useTheme();
  
  const bgColor = backgroundColor || (theme === 'dark' ? 'bg-[#060819]' : 'bg-white');
  const innerBg = theme === 'dark' ? '#060819' : '#ffffff';
  return (
    <div
      className={`w-full rounded-2xl border border-transparent ${bgColor} ${className}`}
      style={{
        backgroundImage: `
          linear-gradient(${gradientAngle}, ${innerBg}, ${innerBg} 100%),
          conic-gradient(
            from ${gradientAngle},
            ${theme === 'dark' ? 'rgba(71, 85, 105, 0.48)' : 'rgba(156, 163, 175, 0.48)'} 80%,
            #FFD700 86%,
            #FFE4B5 90%,
            #FFD700 94%,
            ${theme === 'dark' ? 'rgba(71, 85, 105, 0.48)' : 'rgba(156, 163, 175, 0.48)'}
          )
        `,
        backgroundOrigin: 'border-box',
        backgroundClip: 'padding-box, border-box',
      }}
    >
      {children}
    </div>
  );
};

export default GradientBorder;