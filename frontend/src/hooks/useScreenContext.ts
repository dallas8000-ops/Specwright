import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { ScreenContextResponse } from "@/types/meaning";

export type ScreenName =
  | "dashboard"
  | "cases"
  | "approvals"
  | "runs"
  | "memory"
  | "compliance"
  | "audit"
  | "templates"
  | "integrations"
  | "workflows";

export function useScreenContext(screen: ScreenName) {
  return useQuery({
    queryKey: ["screen-context", screen],
    queryFn: async () =>
      (await api.get<ScreenContextResponse>(`/screen-context/${screen}/`)).data.context,
    staleTime: 20_000,
  });
}
