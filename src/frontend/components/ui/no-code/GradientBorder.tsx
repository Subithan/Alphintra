import React from 'react';

interface GradientBorderProps {
  children: React.ReactNode;
  gradientAngle: '45deg' | '135deg' | '225deg' | '275deg' | '315deg';
  backgroundColor?: string;
  className?: string;
}

const GradientBorder: React.FC<GradientBorderProps> = ({
  children,
  gradientAngle,
  backgroundColor = 'bg-[#060819]',
  className = '',
}) => {
  return (
    <div
      className={`w-full  rounded-2xl border border-transparent ${backgroundColor} ${className}`}
      style={{
        backgroundImage: `
          linear-gradient(${gradientAngle}, #060819, #060819 100%),
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