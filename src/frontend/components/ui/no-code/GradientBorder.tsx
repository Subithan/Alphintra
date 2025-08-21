import React from 'react';
import { theme } from './theme';

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
      className={`w-full  rounded-2xl border border-transparent ${className}`}
      style={{
        backgroundImage: `
          linear-gradient(${gradientAngle}, ${theme.colors.dark.card}, ${theme.colors.dark.card} 100%),
          conic-gradient(
            from ${gradientAngle},
            rgba(71, 85, 105, 0.48) 80%,
            ${theme.colors.gold} 86%,
            #FFE4B5 90%,
            ${theme.colors.gold} 94%,
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