import type { LucideIcon } from "lucide-react";
import { Braces, CreditCard, FolderGit2, LayoutDashboard } from "lucide-react";

export type SpecwrightNavItem = {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
  external?: boolean;
};

export const SPECWRIGHT_NAV: SpecwrightNavItem[] = [
  { to: "/dashboard", label: "Team", icon: LayoutDashboard },
  { to: "/", label: "Connect", icon: FolderGit2, end: true },
  { to: "/billing", label: "Billing", icon: CreditCard },
  { to: "/api", label: "API", icon: Braces },
];
