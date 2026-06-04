import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, Play, Pencil } from "lucide-react";
import { api, Paginated } from "@/api/client";
import ScreenContext from "@/components/context/ScreenContext";
import { useScreenContext } from "@/hooks/useScreenContext";
import type { Workflow } from "@/types";
import styles from "./WorkflowsPage.module.css";

export default function WorkflowsPage() {
  const { data: screenCtx, isLoading: ctxLoading } = useScreenContext("workflows");
  const { data, isLoading } = useQuery({
    queryKey: ["workflows"],
    queryFn: async () => (await api.get<Paginated<Workflow>>("/workflows/")).data,
  });

  async function runWorkflow(slug: string) {
    await api.post(`/workflows/${slug}/run/`, { input: {} });
    alert("Playbook started — check Execution log for meaning per run.");
  }

  return (
    <div className={styles.page}>
      <ScreenContext title="Playbooks" context={screenCtx} loading={ctxLoading} />
      <div className={styles.header}>
        <Link to="/templates" className={styles.primary}>
          <Plus size={16} />
          From library
        </Link>
      </div>
      {isLoading && <p className={styles.muted}>Loading…</p>}
      <div className={styles.list}>
        {data?.results.map((w) => (
          <article key={w.id} className={styles.card}>
            <div>
              <h3>{w.name}</h3>
              <p><strong>What:</strong> {w.status === "active" ? "Live in production" : `Draft — not protecting ops yet`}</p>
              <p><strong>Why:</strong> {w.description || "Automates handoffs between systems and sign-offs."}</p>
              <p><strong>Next:</strong> {w.status === "active" ? "Run with real input or bind to case intake." : "Publish when Legal/HR signs off on steps."}</p>
              <div className={styles.meta}>
                <span className={styles[`status_${w.status}`]}>{w.status}</span>
                {w.department_name && <span>{w.department_name}</span>}
              </div>
            </div>
            <div className={styles.actions}>
              <Link to={`/workflows/${w.slug}/builder`}>
                <Pencil size={14} /> Edit
              </Link>
              {w.status === "active" && (
                <button type="button" onClick={() => runWorkflow(w.slug)}>
                  <Play size={14} /> Run
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
