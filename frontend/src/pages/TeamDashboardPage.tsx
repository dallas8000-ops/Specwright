import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  LayoutDashboard,
  Minus,
  Plus,
} from "lucide-react";
import { fetchTeamDashboard } from "@/api/specwright";
import styles from "./TeamDashboardPage.module.css";

export default function TeamDashboardPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["team-dashboard"],
    queryFn: fetchTeamDashboard,
    refetchInterval: 60_000,
  });

  if (isLoading || !data) {
    return (
      <main className={styles.page}>
        <p className={styles.loading}>Loading team dashboard…</p>
      </main>
    );
  }

  const { summary, projects, drifted_this_week, team_trend, project_trends } = data;
  const maxTrend = Math.max(...team_trend.map((w) => w.avg_score), 1);

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div>
          <p className={styles.eyebrow}>
            <LayoutDashboard size={16} /> Engineering overview
          </p>
          <h1>Team dashboard</h1>
          <p className={styles.lead}>
            All repos, Specwright Scores, and spec drift in one place — built for leads
            managing multiple codebases.
          </p>
        </div>
        <Link to="/" className={styles.connectLink}>
          <Plus size={16} /> Connect repo
        </Link>
      </header>

      <div className={styles.summaryGrid}>
        <SummaryCard label="Projects" value={String(summary.total_projects)} />
        <SummaryCard
          label="Avg Specwright Score"
          value={summary.avg_score != null ? `${summary.avg_score}` : "—"}
          hint="/ 100"
        />
        <SummaryCard
          label="Drifted this week"
          value={String(summary.drifted_this_week)}
          tone={summary.drifted_this_week > 0 ? "warning" : "success"}
        />
        <SummaryCard
          label="Avg doc coverage"
          value={
            summary.avg_documentation_pct != null
              ? `${summary.avg_documentation_pct}%`
              : "—"
          }
        />
        <SummaryCard
          label="Avg test coverage"
          value={
            summary.avg_test_coverage_pct != null
              ? `${summary.avg_test_coverage_pct}%`
              : "—"
          }
        />
        <SummaryCard
          label="Needs attention"
          value={String(summary.needs_attention)}
          tone={summary.needs_attention > 0 ? "warning" : "muted"}
        />
      </div>

      {drifted_this_week.length > 0 && (
        <section className={styles.driftSection}>
          <h2>
            <AlertTriangle size={18} /> Drifted or stale this week
          </h2>
          <ul className={styles.driftList}>
            {drifted_this_week.map((p) => (
              <li key={p.id}>
                <button type="button" onClick={() => navigate(`/project/${p.id}`)}>
                  <strong>{p.name}</strong>
                  <span className={styles.driftReason}>{p.reason}</span>
                  {p.score != null && <span className={styles.scorePill}>{p.score}</span>}
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {team_trend.length > 0 && (
        <section className={styles.trendSection}>
          <h2>Team score trend</h2>
          <p className={styles.trendSub}>Average Specwright Score across scans per week</p>
          <div className={styles.barChart}>
            {team_trend.map((w) => (
              <div key={w.week} className={styles.barCol}>
                <div
                  className={styles.bar}
                  style={{ height: `${(w.avg_score / maxTrend) * 100}%` }}
                  title={`${w.avg_score} avg · ${w.scan_count} scans`}
                />
                <span className={styles.barLabel}>{w.label}</span>
                <span className={styles.barScore}>{w.avg_score}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className={styles.tableSection}>
        <h2>All projects</h2>
        <div className={styles.tableWrap}>
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Score</th>
                <th>7d Δ</th>
                <th>Docs</th>
                <th>Tests</th>
                <th>Spec</th>
                <th>Last scan</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr
                  key={p.id}
                  className={p.needs_attention ? styles.rowAlert : undefined}
                  onClick={() => navigate(`/project/${p.id}`)}
                >
                  <td>
                    <strong>{p.name}</strong>
                    <code>{p.github_repo || shortenPath(p.root_path)}</code>
                  </td>
                  <td>
                    <ScoreBadge score={p.score} grade={p.grade} />
                  </td>
                  <td>
                    <Delta value={p.score_delta_7d} />
                  </td>
                  <td>{pct(p.documentation_pct)}</td>
                  <td>{pct(p.test_coverage_pct)}</td>
                  <td>
                    <span
                      className={
                        p.spec_in_sync ? styles.syncOk : styles.syncBad
                      }
                    >
                      {p.spec_in_sync ? "In sync" : `Drift ${p.commits_behind}`}
                    </span>
                  </td>
                  <td className={styles.muted}>
                    {p.last_scanned_at ? formatRelative(p.last_scanned_at) : "Never"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {projects.length === 0 && (
          <p className={styles.empty}>
            No projects yet. <Link to="/">Connect your first codebase</Link>.
          </p>
        )}
      </section>

      {project_trends.length > 0 && (
        <section className={styles.sparkSection}>
          <h2>Per-repo score history</h2>
          <ul className={styles.sparkGrid}>
            {project_trends.map((pt) => (
              <li key={pt.project_id}>
                <Link to={`/project/${pt.project_id}`}>
                  <span className={styles.sparkName}>{pt.project_name}</span>
                  <Sparkline points={pt.points.map((x) => x.score)} />
                  <span className={styles.sparkLatest}>
                    {pt.points[pt.points.length - 1]?.score ?? "—"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}

function SummaryCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "warning" | "success" | "muted";
}) {
  return (
    <article className={`${styles.summaryCard} ${styles[`tone_${tone}`]}`}>
      <span className={styles.summaryLabel}>{label}</span>
      <strong className={styles.summaryValue}>
        {value}
        {hint && <small>{hint}</small>}
      </strong>
    </article>
  );
}

function ScoreBadge({ score, grade }: { score: number | null; grade?: string | null }) {
  if (score == null) return <span className={styles.na}>—</span>;
  const tone = score >= 85 ? "good" : score >= 65 ? "mid" : "low";
  return (
    <span className={`${styles.scoreBadge} ${styles[`score_${tone}`]}`}>
      {score}
      {grade && <small>{grade}</small>}
    </span>
  );
}

function Delta({ value }: { value: number | null | undefined }) {
  if (value == null) return <span className={styles.muted}>—</span>;
  if (value === 0) return <Minus size={14} className={styles.muted} />;
  if (value > 0) {
    return (
      <span className={styles.deltaUp}>
        <ArrowUpRight size={14} />+{value}
      </span>
    );
  }
  return (
    <span className={styles.deltaDown}>
      <ArrowDownRight size={14} />
      {value}
    </span>
  );
}

function Sparkline({ points }: { points: number[] }) {
  const max = Math.max(...points, 1);
  return (
    <div className={styles.sparkline}>
      {points.map((s, i) => (
        <span
          key={i}
          style={{ height: `${(s / max) * 100}%` }}
          title={String(s)}
        />
      ))}
    </div>
  );
}

function pct(n: number | null | undefined) {
  if (n == null) return "—";
  return `${Math.round(n)}%`;
}

function shortenPath(path: string) {
  if (path.length <= 42) return path;
  return "…" + path.slice(-40);
}

function formatRelative(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
