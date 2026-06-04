import { useQuery } from "@tanstack/react-query";
import { Activity, CheckCircle2, AlertTriangle, FolderOpen } from "lucide-react";
import { api, Paginated } from "@/api/client";
import ScreenContext from "@/components/context/ScreenContext";
import { useScreenContext } from "@/hooks/useScreenContext";
import { useWorkspace } from "@/hooks/useWorkspace";
import AIIntake from "@/components/AIIntake";
import type { ApprovalRequest, Case, ProactiveAlert } from "@/types";
import styles from "./DashboardPage.module.css";

export default function DashboardPage() {
  const { data: me } = useWorkspace();
  const { data: screenCtx, isLoading: ctxLoading } = useScreenContext("dashboard");
  const labels = me?.workspace?.experience?.stat_labels ?? {};

  const { data: cases } = useQuery({
    queryKey: ["cases"],
    queryFn: async () => (await api.get<Paginated<Case>>("/cases/")).data,
  });
  const { data: approvals } = useQuery({
    queryKey: ["approvals"],
    queryFn: async () => (await api.get<Paginated<ApprovalRequest>>("/approvals/?status=pending")).data,
  });
  const { data: alerts } = useQuery({
    queryKey: ["alerts"],
    queryFn: async () => (await api.get<Paginated<ProactiveAlert>>("/alerts/?acknowledged=false")).data,
  });

  const openCases = cases?.results.filter((c) => c.stage !== "post_review").length ?? 0;
  const pending = approvals?.results.length ?? 0;
  const headsUp = alerts?.results.length ?? 0;

  const stats = [
    { label: labels.cases ?? "Open cases", value: openCases, icon: FolderOpen, color: "var(--accent)" },
    { label: labels.approvals ?? "Pending sign-offs", value: pending, icon: CheckCircle2, color: "var(--warning)" },
    { label: labels.alerts ?? "Heads-ups", value: headsUp, icon: AlertTriangle, color: "var(--danger)" },
    { label: "Playbooks active", value: "—", icon: Activity, color: "var(--logistics)" },
  ];

  return (
    <div className={styles.page}>
      <ScreenContext
        title={me?.workspace?.experience?.app_title ?? "Home"}
        context={screenCtx}
        loading={ctxLoading}
      />
      <AIIntake />
      <div className={styles.grid}>
        {stats.map((s) => (
          <article key={s.label} className={styles.stat}>
            <s.icon size={22} style={{ color: s.color }} />
            <div>
              <span className={styles.value}>{s.value}</span>
              <span className={styles.label}>{s.label}</span>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
