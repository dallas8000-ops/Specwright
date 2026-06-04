import { useQuery } from "@tanstack/react-query";
import { api, Paginated } from "@/api/client";
import ScreenContext from "@/components/context/ScreenContext";
import { useScreenContext } from "@/hooks/useScreenContext";
import styles from "./TemplatesPage.module.css";

interface WorkflowTemplate {
  id: number;
  name: string;
  slug: string;
  category: string;
  description: string;
  definition: { nodes?: unknown[]; edges?: unknown[] };
}

const CATEGORY_WHY: Record<string, string> = {
  hr: "Standardizes hire timing — reduces day-one access gaps.",
  legal: "Forces counsel path on high-value deals before signature.",
  logistics: "Cuts mean-time-to-recover on carrier delays.",
};

export default function TemplatesPage() {
  const { data: screenCtx, isLoading: ctxLoading } = useScreenContext("templates");
  const { data } = useQuery({
    queryKey: ["templates"],
    queryFn: async () => (await api.get<Paginated<WorkflowTemplate>>("/workflow-templates/")).data,
  });

  return (
    <div>
      <ScreenContext title="Playbook library" context={screenCtx} loading={ctxLoading} />
      <div className={styles.grid}>
        {data?.results.map((t) => (
          <article
            key={t.id}
            className={styles.card}
            style={{ borderLeftColor: `var(--${t.category === "logistics" ? "logistics" : t.category === "legal" ? "legal" : "hr"})` }}
          >
            <span className={styles.cat}>{t.category}</span>
            <h3>{t.name}</h3>
            <p><strong>What:</strong> {t.description}</p>
            <p><strong>Why:</strong> {CATEGORY_WHY[t.category] ?? "Proven path beats one-off automation."}</p>
            <p><strong>Next:</strong> Publish as active playbook, then bind intake from Cases.</p>
            <footer>
              {t.definition.nodes?.length ?? 0} steps · {t.definition.edges?.length ?? 0} connections
            </footer>
          </article>
        ))}
      </div>
    </div>
  );
}
