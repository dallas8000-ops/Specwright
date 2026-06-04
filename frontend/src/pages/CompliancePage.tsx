import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, Paginated } from "@/api/client";
import ScreenContext from "@/components/context/ScreenContext";
import { useScreenContext } from "@/hooks/useScreenContext";
import { VERTICAL_TERMS } from "@/domain/copy";
import styles from "./CompliancePage.module.css";

interface Report {
  id: number;
  title: string;
  report_type: string;
  created_at: string;
}

interface AccessReview {
  id: number;
  name: string;
  next_review_at: string;
  cadence_days: number;
}

export default function CompliancePage() {
  const qc = useQueryClient();
  const { data: screenCtx, isLoading: ctxLoading } = useScreenContext("compliance");
  const [reportType, setReportType] = useState("soc2_audit");
  const { data: reports } = useQuery({
    queryKey: ["compliance-reports"],
    queryFn: async () => (await api.get<Paginated<Report>>("/compliance-reports/")).data,
  });
  const { data: schedules } = useQuery({
    queryKey: ["access-reviews"],
    queryFn: async () => (await api.get<Paginated<AccessReview>>("/access-reviews/")).data,
  });

  const generate = useMutation({
    mutationFn: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 30);
      return api.post("/compliance-reports/generate/", {
        report_type: reportType,
        period_start: start.toISOString().slice(0, 10),
        period_end: end.toISOString().slice(0, 10),
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["compliance-reports"] }),
  });

  return (
    <div>
      <ScreenContext
        title="Compliance console"
        context={screenCtx}
        loading={ctxLoading}
        onAction={(a) => {
          if (a.action === "generate_soc2") {
            setReportType("soc2_audit");
            generate.mutate();
          }
        }}
      />

      <section className={styles.generate}>
        <h3>One-click {VERTICAL_TERMS.complianceReport}</h3>
        <div className={styles.row}>
          <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
            <option value="soc2_audit">SOC 2 audit trail (CC6/CC7)</option>
            <option value="approval_chain">Approval chain evidence</option>
          </select>
          <button type="button" onClick={() => generate.mutate()} disabled={generate.isPending}>
            Generate report
          </button>
        </div>
      </section>

      <section>
        <h3>Scheduled access reviews</h3>
        {schedules?.results.map((s) => (
          <article key={s.id} className={styles.schedule}>
            <div>
              <strong>{s.name}</strong>
              <p>
                <strong>What:</strong> Review due every {s.cadence_days} days · Next: {s.next_review_at}
              </p>
              <p>
                <strong>Why:</strong> Missed reviews become SOC 2 observations in your next audit.
              </p>
              <p>
                <strong>Next:</strong> Export user list, validate with managers, revoke stale access in IAM.
              </p>
            </div>
          </article>
        ))}
      </section>

      <section>
        <h3>Generated reports</h3>
        {reports?.results.map((r) => (
          <article key={r.id} className={styles.report}>
            <div>
              <strong>{r.title}</strong>
              <span>{new Date(r.created_at).toLocaleString()}</span>
            </div>
            <button
              type="button"
              className={styles.exportBtn}
              onClick={async () => {
                const res = await api.get(`/compliance-reports/${r.id}/export/`, { responseType: "blob" });
                const url = URL.createObjectURL(res.data);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${r.title}.json`;
                a.click();
              }}
            >
              Export JSON
            </button>
          </article>
        ))}
      </section>
    </div>
  );
}
