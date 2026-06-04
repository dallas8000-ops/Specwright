import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, Paginated } from "@/api/client";
import ScreenContext from "@/components/context/ScreenContext";
import MeaningStrip from "@/components/context/MeaningStrip";
import { useScreenContext } from "@/hooks/useScreenContext";
import type { WorkflowRun } from "@/types";
import styles from "./RunsPage.module.css";

const STATUS_CLASS: Record<string, string> = {
  completed: styles.success,
  failed: styles.failed,
  running: styles.running,
  waiting: styles.waiting,
};

export default function RunsPage() {
  const { data: screenCtx, isLoading: ctxLoading } = useScreenContext("runs");
  const { data, isLoading } = useQuery({
    queryKey: ["runs"],
    queryFn: async () => (await api.get<Paginated<WorkflowRun>>("/runs/")).data,
  });

  return (
    <div>
      <ScreenContext title="Execution log" context={screenCtx} loading={ctxLoading} />
      <div className={styles.runList}>
        {data?.results.map((run) => (
          <article key={run.id} className={styles.runCard}>
            <div className={styles.runHead}>
              <strong>{run.workflow_name}</strong>
              <span className={STATUS_CLASS[run.status] ?? ""}>{run.status}</span>
              <time>{new Date(run.started_at).toLocaleString()}</time>
            </div>
            {run.meaning && <MeaningStrip meaning={run.meaning} compact />}
            {run.status === "waiting" && (
              <Link to="/approvals" className={styles.link}>
                Clear blocking sign-off →
              </Link>
            )}
          </article>
        ))}
      </div>
      {isLoading && <p className={styles.muted}>Loading…</p>}
    </div>
  );
}
