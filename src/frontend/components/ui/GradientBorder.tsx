"use client";

import React from 'react';
import clsx from 'clsx';

interface GradientBorderProps {
  children: React.ReactNode;
  gradientAngle: '45deg' | '135deg' | '225deg' | '275deg' | '315deg';
  className?: string;
}

const GradientBorder: React.FC<GradientBorderProps> = ({
  children,
  gradientAngle,
  className = '',
}) => {
  return (
    <div
      className={clsx(
        'w-full rounded-2xl border border-transparent bg-background',
        className
      )}
      style={{
        backgroundImage: `
          linear-gradient(${gradientAngle}, hsl(var(--background)), hsl(var(--background)) 100%),
          conic-gradient(
            from ${gradientAngle},
            rgba(71, 85, 105, 0.48) 80%,
            #FFD700 86%,
            #FFE4B5 90%,
            #FFD700 94%,
            rgba(71, 85, 105, 0.48)
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
