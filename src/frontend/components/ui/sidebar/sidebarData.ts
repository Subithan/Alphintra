// components/sidebar/sidebarData.ts

import { SidebarItemType } from "./types";

export const mainSidebarItems: SidebarItemType[] = [
  {
    id: "dashboard",
    name: "Dashboard",
    icon: "solar:widget-add-line-duotone",
    url: "/dashboard",
  },
  {
    id: "trade",
    name: "Trade",
    icon: "solar:graph-new-up-line-duotone",
    url: "/trade",
  },
  {
    id: "strategy",
    name: "Library",
    icon: "solar:library-line-duotone",
    url: "/strategy",
  },
  {
    id: "market",
    name: "Market",
    icon: "solar:chart-line-duotone",
    url: "/marketplace",
  },
  {
    id: "wallet",
    name: "Wallet",
    icon: "solar:wallet-line-duotone",
    url: "/wallet",
  },
  {
    id: "subscriptions",
    name: "Subscriptions",
    icon: "solar:card-line-duotone",
    url: "#",
    isModal: true,
  },
  {
    id: "ticketing",
    name: "Ticketing",
    icon:  "solar:ticket-line-duotone",
    url: "/support",
  },
  {
    id: "no-code-console",
    name: "Strategy Hub",
    icon: "solar:programming-line-duotone",
    url: "/strategy-hub",
  },
];

export const footerSidebarItems: SidebarItemType[] = [
  {
    id: "settings",
    name: "Settings",
    icon: "solar:settings-line-duotone",
    url: "/profile",
  },
  {
    id: "logout",
    name: "Logout",
    icon: "solar:logout-line-duotone",
    url: "/",
  },
];