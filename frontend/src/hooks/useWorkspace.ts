import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { User } from "@/types";

export interface WorkspaceExperience {
  app_title: string;
  tagline?: string;
  vertical?: string;
  greeting: string;
  primary_action: { label: string; case_type: string; use_ai_intake?: boolean };
  nav: string[];
  stat_labels: Record<string, string>;
  enabled_case_types?: string[];
}

export interface MeResponse extends User {
  workspace: {
    persona: string;
    experience: WorkspaceExperience;
    organization: string | null;
    department: string | null;
    department_type: string | null;
  };
}

export function useWorkspace() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => (await api.get<MeResponse>("/auth/me/")).data,
    staleTime: 60_000,
  });
}
