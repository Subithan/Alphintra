// components/sidebar/sidebarData.ts
import { SidebarItemType } from "../types";

export const mainSidebarItems: SidebarItemType[] = [
  {
    id: "dashboard",
    name: "Dashboard",
    icon: "solar:widget-add-line-duotone",
    url: "/support",
  },
    {
    id: "User Potal",
    name: "User Potal",
    icon:"solar:user-line-duotone",
    url: "/user-portal",
  },
  {
    id: "Ticketing",
    name: "Ticketing",
    icon: "solar:ticket-line-duotone",
    url: "/ticketing",
  },
  {
    id: "KnowledgeBase",
    name: "KnowledgeBase",
    icon: "solar:notebook-minimalistic-line-duotone",
    url: "/knowledge-base",
  },
  {
    id: "Escalation",
    name: "Escalation",
    icon: "solar:danger-triangle-line-duotone",
    url: "/escalation",
  },
  {
    id: "Troubleshooting",
    name: "Troubleshooting",
    icon: "solar:shield-plus-line-duotone",
    url: "/troubleshooting",
  },
  {
    id: "Marketplace",
    name: "Marketplace",
    icon: "solar:server-minimalistic-line-duotone",
    url: "/market-place",
  },
];

export const footerSidebarItems: SidebarItemType[] = [
  {
    id: "settings",
    name: "Settings",
    icon: "solar:settings-outline",
    url: "/support-settings",
  },
  {
    id: "logout",
    name: "Logout",
    icon: "solar:logout-outline",
    url: "/",
  },
];