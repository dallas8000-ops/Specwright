import { useQuery } from "@tanstack/react-query";
import { api, Paginated } from "@/api/client";
import ScreenContext from "@/components/context/ScreenContext";
import { useScreenContext } from "@/hooks/useScreenContext";
import styles from "./IntegrationsPage.module.css";

interface Connector {
  id: number;
  name: string;
  kind: string;
  description: string;
}

const DEEP_VALUE: Record<string, string> = {
  slack: "Heads-ups ship with Acknowledge/Escalate — not vanity #general posts.",
  docusign: "Envelopes fire only after Legal sign-off — audit chain intact.",
  workday: "Hire events sync after HR clearance — no phantom employees in payroll.",
  rest: "Calls are logged with latency and status — failures are diagnosable.",
};

export default function IntegrationsPage() {
  const { data: screenCtx, isLoading: ctxLoading } = useScreenContext("integrations");
  const { data } = useQuery({
    queryKey: ["connectors"],
    queryFn: async () => (await api.get<Paginated<Connector>>("/connectors/")).data,
  });

  return (
    <div>
      <ScreenContext title="Connections" context={screenCtx} loading={ctxLoading} />
      <div className={styles.grid}>
        {data?.results.map((c) => (
          <article key={c.id} className={styles.card}>
            <span className={styles.kind}>{c.kind}</span>
            <h3>{c.name}</h3>
            <p><strong>What:</strong> {c.description}</p>
            <p><strong>Why:</strong> {DEEP_VALUE[c.kind] ?? DEEP_VALUE.rest}</p>
            <p><strong>Next:</strong> Store credentials under org settings before next playbook run.</p>
          </article>
        ))}
      </div>
    </div>
  );
}
