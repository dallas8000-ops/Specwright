import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { api } from "@/api/client";
import { useWorkspace } from "@/hooks/useWorkspace";
import styles from "./AIIntake.module.css";

export default function AIIntake() {
  const { data: me } = useWorkspace();
  const qc = useQueryClient();
  const [description, setDescription] = useState("");

  const intake = useMutation({
    mutationFn: () => api.post("/ai/intake/", { description }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases"] });
      qc.invalidateQueries({ queryKey: ["ai-assessments"] });
      setDescription("");
    },
  });

  const action = me?.workspace?.experience?.primary_action;

  return (
    <section className={styles.panel}>
      <div className={styles.head}>
        <Sparkles size={18} />
        <div>
          <h3>AI intake</h3>
          <p>Describe the situation — AI structures the matter and runs triage. Not a blank form.</p>
        </div>
      </div>
      <textarea
        rows={3}
        placeholder={
          action?.use_ai_intake
            ? `e.g. ${action.label.replace(" (AI intake)", "")}…`
            : "Describe what happened in plain language…"
        }
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <button
        type="button"
        disabled={!description.trim() || intake.isPending}
        onClick={() => intake.mutate()}
      >
        {intake.isPending ? "AI processing…" : action?.label ?? "Open with AI"}
      </button>
      {intake.isError && (
        <p className={styles.err}>Could not process — check vertical allows this case type.</p>
      )}
    </section>
  );
}
