import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Brain, Bell } from "lucide-react";
import { api, Paginated } from "@/api/client";
import ScreenContext from "@/components/context/ScreenContext";
import MeaningStrip from "@/components/context/MeaningStrip";
import { useScreenContext } from "@/hooks/useScreenContext";
import { VERTICAL_TERMS } from "@/domain/copy";
import type { MeaningAction } from "@/types/meaning";
import styles from "./MemoryPage.module.css";

interface Insight {
  id: number;
  title: string;
  meaning?: import("@/types/meaning").MeaningContext;
}

interface Alert {
  id: number;
  title: string;
  meaning?: import("@/types/meaning").MeaningContext;
}

export default function MemoryPage() {
  const qc = useQueryClient();
  const { data: screenCtx, isLoading: ctxLoading } = useScreenContext("memory");
  const { data: insights } = useQuery({
    queryKey: ["insights"],
    queryFn: async () => (await api.get<Paginated<Insight>>("/insights/")).data,
  });
  const { data: alerts } = useQuery({
    queryKey: ["alerts"],
    queryFn: async () => (await api.get<Paginated<Alert>>("/alerts/?acknowledged=false")).data,
  });

  const ack = useMutation({
    mutationFn: (id: number) => api.post(`/alerts/${id}/acknowledge/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
  const esc = useMutation({
    mutationFn: (id: number) => api.post(`/alerts/${id}/escalate/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
  const scan = useMutation({
    mutationFn: () => api.post("/alerts/refresh-scan/"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["insights"] });
      qc.invalidateQueries({ queryKey: ["alerts"] });
      qc.invalidateQueries({ queryKey: ["screen-context"] });
    },
  });

  function handleAlertAction(id: number, action: MeaningAction) {
    if (action.action === "acknowledge") ack.mutate(id);
    if (action.action === "escalate") esc.mutate(id);
  }

  return (
    <div>
      <ScreenContext
        title={VERTICAL_TERMS.memory}
        context={screenCtx}
        loading={ctxLoading}
        onAction={(a) => a.action === "refresh_scan" && scan.mutate()}
      />

      <section>
        <h3>
          <Bell size={18} /> Proactive {VERTICAL_TERMS.proactiveAlert}s
        </h3>
        <div className={styles.list}>
          {alerts?.results.map((a) => (
            <article key={a.id} className={styles.alert}>
              <h4>{a.title}</h4>
              {a.meaning && (
                <MeaningStrip meaning={a.meaning} onAction={(act) => handleAlertAction(a.id, act)} />
              )}
            </article>
          ))}
          {!alerts?.results.length && <p className={styles.muted}>No active heads-ups.</p>}
        </div>
      </section>

      <section>
        <h3>
          <Brain size={18} /> Patterns we remember
        </h3>
        <div className={styles.list}>
          {insights?.results.map((i) => (
            <article key={i.id} className={styles.insight}>
              <h4>{i.title}</h4>
              {i.meaning && <MeaningStrip meaning={i.meaning} compact />}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
