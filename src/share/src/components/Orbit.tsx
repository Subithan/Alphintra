import React, { FC } from 'react'; // Import FC for functional component

interface OrbitProps {
  className?: string; // className is an optional string prop
}

const Orbit: FC<OrbitProps> = ({ className }) => {
  return (
    <svg
      viewBox="0 0 200 200"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        cx="100"
        cy="100"
        r="80"
        stroke="currentColor"
        strokeWidth="1"
        strokeDasharray="4 4"
        className="animate-spin-slow opacity-30"
      />
    </svg>
  );
};

export default Orbit;