import { useQuery } from "@tanstack/react-query";
import { api, Paginated } from "@/api/client";
import ScreenContext from "@/components/context/ScreenContext";
import { useScreenContext } from "@/hooks/useScreenContext";
import { VERTICAL_TERMS } from "@/domain/copy";
import styles from "./RunsPage.module.css";

interface AuditLog {
  id: number;
  actor_name: string;
  action: string;
  resource_type: string;
  resource_id: string;
  created_at: string;
}

function auditMeaning(log: AuditLog) {
  const what = `${log.action} on ${log.resource_type} #${log.resource_id}`;
  const who = log.actor_name || "system";
  const why =
    log.action === "approve"
      ? "Proves authorized sign-off for auditors and Legal."
      : log.action === "reject"
        ? "Documents why automation was stopped — liability containment."
        : "Immutable evidence — always on, never toggled per user.";
  const next =
    log.action === "approve" || log.action === "reject"
      ? "Correlate with the related case or sign-off in Compliance export."
      : "No action unless investigating an incident.";
  return { what, who, why, next };
}

export default function AuditPage() {
  const { data: screenCtx, isLoading: ctxLoading } = useScreenContext("audit");
  const { data } = useQuery({
    queryKey: ["audit"],
    queryFn: async () => (await api.get<Paginated<AuditLog>>("/audit-logs/")).data,
  });

  return (
    <div>
      <ScreenContext title={VERTICAL_TERMS.auditTrail} context={screenCtx} loading={ctxLoading} />
      <div className={styles.runList}>
        {data?.results.map((log) => {
          const m = auditMeaning(log);
          return (
            <article key={log.id} className={styles.runCard}>
              <div className={styles.runHead}>
                <strong>{m.what}</strong>
                <time>{new Date(log.created_at).toLocaleString()}</time>
              </div>
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.35rem" }}>
                <strong>Who:</strong> {m.who} · <strong>Why:</strong> {m.why}
              </p>
              <p style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>
                <strong>Next:</strong> {m.next}
              </p>
            </article>
          );
        })}
      </div>
    </div>
  );
}
