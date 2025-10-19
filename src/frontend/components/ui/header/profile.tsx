"use client";
import { useState, useRef, useEffect } from "react";
import Link from "next/link";

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
const generateAvatarSvg = (name: string, size: number = 36): string => {
  const initials = getInitials(name);
  const fontSize = Math.floor(size * 0.5);
  
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

// Get user info from localStorage
const getUserName = (): string => {
  if (typeof window === 'undefined') return 'User';
  
  try {
    const storedUser = localStorage.getItem('alphintra_jwt_user');
    if (storedUser) {
      const user = JSON.parse(storedUser);
      const fullName = [user.firstName, user.lastName].filter(Boolean).join(' ').trim();
      return fullName || user.username || user.userName || 'User';
    }
  } catch (error) {
    console.error('Failed to parse user data', error);
  }
  
  return 'User';
};

const Profile = () => {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [avatarUrl, setAvatarUrl] = useState<string>('');

  useEffect(() => {
    // Generate avatar from user's name
    const userName = getUserName();
    const generatedAvatar = generateAvatarSvg(userName, 36);
    setAvatarUrl(generatedAvatar);

    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <Link href="/profile">
        <img
          src={avatarUrl}
          alt="Profile"
          width={36}
          height={36}
          className="rounded-full cursor-pointer ring-2 ring-border"
        />
      </Link>
    </div>
  );
};

export default Profile;
