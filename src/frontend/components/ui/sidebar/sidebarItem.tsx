"use client";
import { SidebarItemType } from "./types";
import Link from "next/link";
import { Icon } from "@iconify/react";
import { usePathname, useRouter } from "next/navigation";
import { useSubscriptionModal } from "@/contexts/SubscriptionModalContext";

interface Props {
  item: SidebarItemType;
  collapsed?: boolean;
}

const SidebarItem = ({ item, collapsed = false }: Props) => {
  const pathname = usePathname();
  const router = useRouter();
  const isActive = pathname === item.url;
  const { openModal } = useSubscriptionModal();

  const handleClick = (e: React.MouseEvent) => {
    if (item.isModal) {
      e.preventDefault();
      openModal();
    } else if (item.id === 'logout') {
      e.preventDefault();
      handleLogout();
    }
  };

  const handleLogout = () => {
    // Clear all authentication data
    if (typeof window !== 'undefined') {
      localStorage.removeItem('alphintra_jwt_token');
      localStorage.removeItem('alphintra_auth_token');
      localStorage.removeItem('auth_token');
      localStorage.removeItem('alphintra_jwt_user');
      localStorage.removeItem('alphintra_wallet_credentials');
      
      // Clear any other session data
      sessionStorage.clear();
      
      console.log('✅ User logged out successfully');
      
      // Redirect to login/home page
      router.push('/');
    }
  };

  return (
    <li
      className={`rounded-md transition ${
        isActive && !item.external && !item.isModal && item.id !== 'logout'
          ? "bg-gradient-to-r from-yellow-500/10 to-transparent border-l-4 border-yellow-500 text-yellow-500"
          : "hover:bg-gradient-to-r hover:from-yellow-500/10 hover:to-transparent hover:border-l-4 hover:border-yellow-500 hover:text-yellow-500"
      }`}
    >
      {item.external ? (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3 px-4 py-2 w-full"
        >
          <Icon icon={item.icon} width="20" />
          {!collapsed && <span className="text-[15px] font-semibold">{item.name}</span>}
          {!collapsed && <Icon icon="solar:external-link-line-duotone" width="14" className="ml-auto opacity-60" />}
        </a>
      ) : item.isModal || item.id === 'logout' ? (
        <button
          onClick={handleClick}
          className="flex items-center gap-3 px-4 py-2 w-full text-left"
        >
          <Icon icon={item.icon} width="20" />
          {!collapsed && <span className="text-[15px] font-semibold">{item.name}</span>}
        </button>
      ) : (
        <Link
          href={item.url}
          className="flex items-center gap-3 px-4 py-2 w-full"
        >
          <Icon icon={item.icon} width="20" />
          {!collapsed && <span className="text-[15px] font-semibold">{item.name}</span>}
        </Link>
      )}
    </li>
  );
};

export default SidebarItem;