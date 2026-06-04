import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, ShieldAlert } from "lucide-react";
import { api } from "@/api/client";
import styles from "./AICaseCopilot.module.css";

interface Assessment {
  id: number;
  result: {
    summary?: string;
    risks?: { severity: string; title: string; detail: string }[];
    recommended_action?: string;
    confidence?: number;
    reasoning?: string;
    draft_communication?: string;
    provider?: string;
  };
  confidence: number;
}

interface CopilotMsg {
  id: number;
  role: string;
  content: string;
}

export default function AICaseCopilot({ caseId }: { caseId: number }) {
  const qc = useQueryClient();
  const [message, setMessage] = useState("");

  const { data: assessments } = useQuery({
    queryKey: ["ai-assessments", caseId],
    queryFn: async () =>
      (await api.get<{ results: Assessment[] }>(`/ai-assessments/?case=${caseId}&kind=triage`)).data
        .results,
  });

  const { data: history } = useQuery({
    queryKey: ["copilot", caseId],
    queryFn: async () =>
      (await api.get<CopilotMsg[]>(`/ai/cases/${caseId}/copilot-history/`)).data,
  });

  const triage = useMutation({
    mutationFn: () => api.post(`/ai/cases/${caseId}/triage/`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["ai-assessments", caseId] });
    },
  });

  const copilot = useMutation({
    mutationFn: () => api.post(`/ai/cases/${caseId}/copilot/`, { message }),
    onSuccess: () => {
      setMessage("");
      qc.invalidateQueries({ queryKey: ["copilot", caseId] });
    },
  });

  const latest = assessments?.[0];

  return (
    <aside className={styles.panel}>
      <header>
        <Bot size={18} />
        <span>AI intervention</span>
        <button type="button" className={styles.triageBtn} onClick={() => triage.mutate()} disabled={triage.isPending}>
          {triage.isPending ? "Analyzing…" : "Run triage"}
        </button>
      </header>

      {latest && (
        <div className={styles.assessment}>
          <p className={styles.summary}>{latest.result.summary}</p>
          {latest.result.risks?.map((r, i) => (
            <div key={i} className={styles.risk}>
              <ShieldAlert size={14} className={styles[r.severity]} />
              <div>
                <strong>{r.title}</strong>
                <p>{r.detail}</p>
              </div>
            </div>
          ))}
          <p className={styles.next}>
            <strong>AI recommends:</strong> {latest.result.recommended_action}
          </p>
          <small>
            Confidence {(latest.confidence * 100).toFixed(0)}% · {latest.result.provider ?? "ai"}
          </small>
        </div>
      )}

      <div className={styles.chat}>
        {history?.map((m) => (
          <div key={m.id} className={m.role === "user" ? styles.user : styles.assistant}>
            {m.content}
          </div>
        ))}
      </div>
      <div className={styles.inputRow}>
        <input
          placeholder="Ask AI: liability exposure? escalate?"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && message.trim() && copilot.mutate()}
        />
        <button type="button" onClick={() => copilot.mutate()} disabled={!message.trim()}>
          Ask
        </button>
      </div>
    </aside>
  );
}
