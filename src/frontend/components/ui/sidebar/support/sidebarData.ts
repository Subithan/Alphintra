// components/sidebar/sidebarData.ts

import { SidebarItemType } from "../types";

export const mainSidebarItems: SidebarItemType[] = [
  {
    id: "dashboard",
    name: "Dashboard",
    icon: "solar:widget-add-line-duotone",
    url: "/support",
  },
];

export const footerSidebarItems: SidebarItemType[] = [
  {
    id: "settings",
    name: "Settings",
    icon: "solar:settings-line-duotone",
    url: "/support-settings",
  },
  {
    id: "logout",
    name: "Logout",
    icon: "solar:logout-line-duotone",
    url: "/logout",
  },
];