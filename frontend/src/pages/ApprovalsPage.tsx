import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, Paginated } from "@/api/client";
import ScreenContext from "@/components/context/ScreenContext";
import MeaningStrip from "@/components/context/MeaningStrip";
import { useScreenContext } from "@/hooks/useScreenContext";
import type { ApprovalRequest } from "@/types";
import type { MeaningAction } from "@/types/meaning";
import styles from "./ApprovalsPage.module.css";

export default function ApprovalsPage() {
  const qc = useQueryClient();
  const { data: screenCtx, isLoading: ctxLoading } = useScreenContext("approvals");
  const { data } = useQuery({
    queryKey: ["approvals"],
    queryFn: async () => (await api.get<Paginated<ApprovalRequest>>("/approvals/")).data,
  });

  const decide = useMutation({
    mutationFn: ({ id, approved }: { id: number; approved: boolean }) =>
      api.post(`/approvals/${id}/decide/`, { approved, note: "" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] });
      qc.invalidateQueries({ queryKey: ["screen-context"] });
    },
  });

  const pending = data?.results.filter((a) => a.status === "pending") ?? [];

  function handleAction(id: number, action: MeaningAction) {
    if (action.action === "approve") decide.mutate({ id, approved: true });
    if (action.action === "reject") decide.mutate({ id, approved: false });
  }

  return (
    <div>
      <ScreenContext title="Sign-off inbox" context={screenCtx} loading={ctxLoading} />
      <div className={styles.list}>
        {pending.map((a) => (
          <article key={a.id} className={styles.card}>
            <h3>{a.title}</h3>
            {a.meaning ? (
              <MeaningStrip meaning={a.meaning} onAction={(act) => handleAction(a.id, act)} />
            ) : (
              <p>{a.workflow_name}</p>
            )}
          </article>
        ))}
        {!pending.length && (
          <p className={styles.muted}>No pending sign-offs — playbooks are unblocked.</p>
        )}
      </div>
    </div>
  );
}
