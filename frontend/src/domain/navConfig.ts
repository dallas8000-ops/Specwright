import {
  LayoutDashboard,
  FolderOpen,
  CheckSquare,
  FileStack,
  Play,
  Plug,
  Shield,
  Brain,
  Scale,
} from "lucide-react";

export type NavKey =
  | "home"
  | "cases"
  | "approvals"
  | "templates"
  | "runs"
  | "integrations"
  | "audit"
  | "compliance"
  | "memory";

export const NAV_ITEMS: Record<
  NavKey,
  { to: string; label: string; icon: typeof LayoutDashboard }
> = {
  home: { to: "/", label: "Home", icon: LayoutDashboard },
  cases: { to: "/cases", label: "Cases", icon: FolderOpen },
  approvals: { to: "/approvals", label: "Sign-offs", icon: CheckSquare },
  templates: { to: "/templates", label: "Playbook library", icon: FileStack },
  runs: { to: "/runs", label: "Execution log", icon: Play },
  integrations: { to: "/integrations", label: "Connections", icon: Plug },
  audit: { to: "/audit", label: "Audit trail", icon: Shield },
  compliance: { to: "/compliance", label: "Compliance", icon: Scale },
  memory: { to: "/memory", label: "Memory & alerts", icon: Brain },
};

export function navForPersona(navKeys: string[]) {
  return navKeys
    .filter((k): k is NavKey => k in NAV_ITEMS)
    .map((k) => NAV_ITEMS[k]);
}
