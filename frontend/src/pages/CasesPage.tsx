import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, Paginated } from "@/api/client";
import ScreenContext from "@/components/context/ScreenContext";
import MeaningStrip from "@/components/context/MeaningStrip";
import { useScreenContext } from "@/hooks/useScreenContext";
import AICaseCopilot from "@/components/AICaseCopilot";
import { CASE_STAGES, VERTICAL_TERMS } from "@/domain/copy";
import type { MeaningAction } from "@/types/meaning";
import styles from "./CasesPage.module.css";

interface CaseItem {
  id: number;
  title: string;
  case_type_label: string;
  stage: string;
  stage_label: string;
  next_stage: string | null;
  subject_label: string;
  priority: string;
  department_name: string;
  meaning: import("@/types/meaning").MeaningContext;
}

export default function CasesPage() {
  const qc = useQueryClient();
  const { data: screenCtx, isLoading: ctxLoading } = useScreenContext("cases");
  const { data } = useQuery({
    queryKey: ["cases"],
    queryFn: async () => (await api.get<Paginated<CaseItem>>("/cases/")).data,
  });

  const advance = useMutation({
    mutationFn: (id: number) => api.post(`/cases/${id}/advance/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["screen-context"] });
    },
  });

  function handleMeaningAction(caseId: number, action: MeaningAction) {
    if (action.action === "advance") advance.mutate(caseId);
  }

  return (
    <div>
      <ScreenContext title={VERTICAL_TERMS.cases} context={screenCtx} loading={ctxLoading} />
      <div className={styles.pipeline}>
        {Object.entries(CASE_STAGES).map(([key, label]) => (
          <span key={key}>{label}</span>
        ))}
      </div>
      <div className={styles.list}>
        {data?.results.map((c) => (
          <article key={c.id} className={styles.card}>
            <header>
              <span className={styles.type}>{c.case_type_label}</span>
              <h3>{c.title}</h3>
              <div className={styles.meta}>
                <span className={styles.stage}>{c.stage_label}</span>
                <span>{c.department_name}</span>
                <span className={styles[c.priority]}>{c.priority}</span>
              </div>
            </header>
            {c.meaning && (
              <MeaningStrip
                meaning={c.meaning}
                onAction={(a) => handleMeaningAction(c.id, a)}
              />
            )}
            <AICaseCopilot caseId={c.id} />
          </article>
        ))}
      </div>
    </div>
  );
}
