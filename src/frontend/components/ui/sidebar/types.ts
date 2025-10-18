// app/ui/dashboard/sidebar/types.ts

export interface SidebarItemType {
  id: string;
  name: string;
  icon: string;
  url: string;
  external?: boolean; // Opens in new tab if true
  isModal?: boolean; // Opens as modal if true
}