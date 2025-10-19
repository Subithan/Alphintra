import React from 'react';

interface ProfileCardProps {
  avatarUrl?: string | null;
  nickname: string;
}

// Extract initials from name (e.g., "John Doe" -> "JD")
const getInitials = (name: string): string => {
  if (!name || name.trim() === '') return '?';
  
  const nameParts = name.trim().split(/\s+/).filter(part => part.length > 0);
  
  if (nameParts.length === 0) return '?';
  if (nameParts.length === 1) return nameParts[0][0].toUpperCase();
  
  const firstInitial = nameParts[0][0].toUpperCase();
  const lastInitial = nameParts[nameParts.length - 1][0].toUpperCase();
  
  return `${firstInitial}${lastInitial}`;
};

// Generate avatar SVG with yellow background and black text
const generateAvatarSvg = (name: string, size: number = 128): string => {
  const initials = getInitials(name);
  const fontSize = Math.floor(size * 0.4);
  
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
      <rect width="${size}" height="${size}" fill="#FCD34D" rx="${size / 2}" />
      <text
        x="50%"
        y="50%"
        dominant-baseline="central"
        text-anchor="middle"
        font-family="system-ui, -apple-system, sans-serif"
        font-size="${fontSize}"
        font-weight="600"
        fill="#000000"
      >
        ${initials}
      </text>
    </svg>
  `;
  
  const base64 = btoa(svg.trim());
  return `data:image/svg+xml;base64,${base64}`;
};

const ProfileCard: React.FC<ProfileCardProps> = ({ avatarUrl, nickname }) => {
  // Use uploaded avatar if available, otherwise generate from initials
  const finalAvatarUrl = avatarUrl && avatarUrl.trim() !== '' 
    ? avatarUrl 
    : generateAvatarSvg(nickname, 160);

  return (
    <div className="flex items-center space-x-4 p-3 pl-10">
      <img
        src={finalAvatarUrl}
        alt={`${nickname}'s avatar`}
        className="w-20 h-20 rounded-full object-cover ring-2 ring-border"
      />
      <span className="text-xl font-semibold text-black dark:text-white">
        {nickname}
      </span>
    </div>
  );
};

export default ProfileCard;
