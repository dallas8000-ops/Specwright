import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import { useWorkspace } from "@/hooks/useWorkspace";
import styles from "./QuickStart.module.css";

export default function QuickStart() {
  const { data: me } = useWorkspace();
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const action = me?.workspace?.experience?.primary_action;

  const openCase = useMutation({
    mutationFn: () =>
      api.post("/cases/quick-open/", {
        case_type: action?.case_type ?? "new_hire",
        title: title || action?.label,
        subject_label: "",
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["cases"] });
      setTitle("");
    },
  });

  if (!action) return null;

  return (
    <section className={styles.panel}>
      <h3>Start here — under 2 minutes</h3>
      <p>{me?.workspace?.experience?.greeting}</p>
      <div className={styles.row}>
        <input
          placeholder={`e.g. ${action.label}…`}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <button type="button" onClick={() => openCase.mutate()} disabled={openCase.isPending}>
          {action.label}
        </button>
      </div>
      <small>No manual. Opens at Intake — stages guide you from there.</small>
    </section>
  );
}
