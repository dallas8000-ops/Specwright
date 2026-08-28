import { useEffect, useRef, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowUpRight,
  BookOpen,
  Code2,
  GitPullRequest,
  Sparkles,
} from "lucide-react";
import { specwright, ProjectHealth } from "@/api/specwright";
import styles from "./HealthDashboard.module.css";

type Props = {
  projectId: number;
  projectName?: string;
  framework?: string;
  lastScannedAt?: string;
  onGenerate?: () => void;
  isGenerating?: boolean;
  onFixTests?: () => void;
  isFixingTests?: boolean;
  onFillDescriptions?: () => void;
  isFillingDescriptions?: boolean;
};

export default function HealthDashboard({
  projectId,
  projectName = "Project",
  framework = "api",
  lastScannedAt,
  onGenerate,
  isGenerating,
  onFixTests,
  isFixingTests,
  onFillDescriptions,
  isFillingDescriptions,
}: Props) {
  const { data: health, isLoading } = useQuery({
    queryKey: ["health", projectId],
    queryFn: async () =>
      (await specwright.get<ProjectHealth>(`/projects/${projectId}/health`)).data,
  });

  const autoFixStarted = useRef(false);
  useEffect(() => {
    if (
      health?.alerts?.test_gap &&
      onFixTests &&
      !autoFixStarted.current &&
      !isFixingTests &&
      !isGenerating
    ) {
      autoFixStarted.current = true;
      onFixTests();
    }
  }, [health?.alerts?.test_gap, onFixTests, isFixingTests, isGenerating]);

  if (isLoading || !health) {
    return (
      <section className={styles.dashboard}>
        <p className={styles.loading}>Calculating Specwright Score…</p>
      </section>
    );
  }

  const score = health.score.score;
  const breakdown = health.score.breakdown;
  const metrics = health.metrics;
  const alerts = health.alerts;
  const scannedLabel = formatRelative(health.last_scanned_at ?? lastScannedAt);
  const modelsCount = health.models_count ?? metrics?.models_documented.total ?? 0;
  const inSync = metrics?.spec_in_sync ?? !health.drift.drift_detected;

  return (
    <section className={styles.dashboard}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.projectTitle}>
            <Code2 size={20} className={styles.titleIcon} />
            {projectName}
            <span className={styles.titleSep}>/</span>
            {framework}
          </h1>
          <p className={styles.meta}>
            Last scanned {scannedLabel} · {health.route_count} routes · {modelsCount} models
          </p>
        </div>
        {inSync && (
          <span className={styles.syncPill}>
            <span aria-hidden>✓</span> Spec in sync
          </span>
        )}
      </header>

      <div className={styles.scoreSection}>
        <ScoreRing score={score} />
        <div className={styles.breakdown}>
          <h2 className={styles.scoreHeading}>Specwright Score</h2>
          <p className={styles.scoreSummary}>{health.score.summary}</p>
          <CategoryBar label="API documentation" value={breakdown.documentation_pct} />
          <CategoryBar label="Test coverage" value={breakdown.test_coverage_pct} />
          <CategoryBar label="Spec freshness" value={breakdown.freshness_pct} />
          <CategoryBar
            label="Model documentation"
            value={breakdown.model_documentation_pct ?? 0}
          />
        </div>
      </div>

      {metrics && (
        <div className={styles.metricGrid}>
          <MetricCard
            title="Routes documented"
            value={`${metrics.routes_documented.current} / ${metrics.routes_documented.total}`}
            tone="success"
            sub={
              metrics.routes_documented_delta > 0
                ? `+${metrics.routes_documented_delta} this scan`
                : "Up to date"
            }
            subIcon={metrics.routes_documented_delta > 0 ? <ArrowUpRight size={14} /> : undefined}
          />
          <MetricCard
            title="Tests generated"
            value={`${metrics.tests_generated.current} / ${metrics.tests_generated.total}`}
            tone={metrics.tests_generated.uncovered > 0 ? "warning" : "success"}
            sub={
              metrics.tests_generated.uncovered > 0
                ? `${metrics.tests_generated.uncovered} routes uncovered`
                : "All routes covered"
            }
          />
          <MetricCard
            title="Models documented"
            value={`${metrics.models_documented.current} / ${metrics.models_documented.total}`}
            tone="muted"
            sub={
              metrics.models_documented.missing > 0
                ? `${metrics.models_documented.missing} missing field docs`
                : "Models complete"
            }
          />
          <MetricCard
            title="Spec drift"
            value={String(metrics.spec_drift)}
            tone={metrics.spec_in_sync ? "success" : "warning"}
            sub={metrics.spec_in_sync ? "Fully synced" : health.drift.message}
          />
        </div>
      )}

      {health.autopilot?.checks && health.autopilot.checks.length > 0 && (
        <div
          className={
            health.autopilot.all_pass ? styles.bannerSuccess : styles.bannerWarning
          }
        >
          <Sparkles size={18} />
          <div>
            <p style={{ margin: 0, fontWeight: 600 }}>
              Autopilot {health.autopilot.all_pass ? "— all checks passed" : "— finishing checks"}
            </p>
            <ul className={styles.autopilotChecks}>
              {health.autopilot.checks.map((c) => (
                <li key={c.id}>
                  <span className={styles.checkStatus}>{c.status}</span>
                  {c.label}
                  {c.detail ? ` (${c.detail})` : ""}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {alerts?.zero_routes && (
        <div className={styles.bannerWarning}>
          <AlertTriangle size={18} />
          <p>{alerts.zero_routes.message}</p>
        </div>
      )}

      {alerts?.test_gap && (
        <div className={styles.bannerWarning}>
          <AlertTriangle size={18} />
          <p>
            {alerts.test_gap.message}{" "}
            <button
              type="button"
              className={styles.bannerAction}
              onClick={onFixTests ?? onGenerate}
              disabled={isFixingTests || isGenerating}
            >
              {isFixingTests || isGenerating
                ? "Fixing tests…"
                : "Fix automatically"}
            </button>
          </p>
        </div>
      )}

      {alerts?.description_gap && onFillDescriptions && (
        <div
          className={
            alerts.description_gap.filled
              ? styles.bannerSuccess
              : styles.bannerWarning
          }
        >
          <BookOpen size={18} />
          <p>
            {alerts.description_gap.message}{" "}
            {!alerts.description_gap.filled && (
              <button
                type="button"
                className={styles.bannerAction}
                onClick={onFillDescriptions}
                disabled={isFillingDescriptions}
              >
                {isFillingDescriptions ? "Filling…" : "Fill descriptions now."}
              </button>
            )}
          </p>
        </div>
      )}

      {alerts?.pr_update && (
        <div className={styles.bannerInfo}>
          <GitPullRequest size={18} />
          <div className={styles.bannerBlock}>
            <p>
              {alerts.pr_update.message}{" "}
              <span className={styles.bannerHint}>Review the diff before merging.</span>
            </p>
            {(alerts.pr_update.migration_note || health.ai?.migration_note) && (
              <div className={styles.migrationNote}>
                <strong>Client migration note</strong>
                <p>{alerts.pr_update.migration_note ?? health.ai?.migration_note}</p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className={styles.routeHealth}>
        <h3>Route health</h3>
        <div className={styles.routeTable}>
          <div className={styles.routeHead}>
            <span>Method</span>
            <span>Endpoint</span>
            <span>Status</span>
          </div>
          {health.coverage.map((row) => {
            const label = row.status_label ?? statusFromFlags(row);
            const tone = labelTone(label, row.status);
            return (
              <div key={`${row.method}-${row.path}`} className={styles.routeRow}>
                <span className={`${styles.method} ${styles[`method_${row.method}`]}`}>
                  {row.method}
                </span>
                <code className={styles.path}>{row.path}</code>
                <span className={styles.statusCell}>
                  <span className={`${styles.statusDot} ${styles[`dot_${tone}`]}`} />
                  {label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {health.synced_files.length > 0 && (
        <p className={styles.synced}>
          <Sparkles size={14} />
          Live sync wrote {health.synced_files.length} file(s) to your repo.
        </p>
      )}
    </section>
  );
}

function ScoreRing({ score }: { score: number }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - Math.min(100, Math.max(0, score)) / 100);

  return (
    <div className={styles.ringWrap}>
      <svg viewBox="0 0 128 128" className={styles.gauge} aria-hidden>
        <circle cx="64" cy="64" r={r} className={styles.gaugeTrack} />
        <circle
          cx="64"
          cy="64"
          r={r}
          className={styles.gaugeFill}
          strokeDasharray={c}
          strokeDashoffset={offset}
          transform="rotate(-90 64 64)"
        />
      </svg>
      <div className={styles.ringCenter}>
        <span className={styles.ringScore}>{score}</span>
        <span className={styles.ringOf}>/ 100</span>
      </div>
    </div>
  );
}

function CategoryBar({ label, value }: { label: string; value: number }) {
  const tone = value >= 85 ? "good" : value >= 65 ? "mid" : "low";
  return (
    <div className={styles.catRow}>
      <span className={styles.catLabel}>{label}</span>
      <div className={styles.catTrack}>
        <div
          className={`${styles.catFill} ${styles[`cat_${tone}`]}`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className={styles.catPct}>{Math.round(value)}%</span>
    </div>
  );
}

function MetricCard({
  title,
  value,
  sub,
  tone,
  subIcon,
}: {
  title: string;
  value: string;
  sub: string;
  tone: "success" | "warning" | "muted";
  subIcon?: ReactNode;
}) {
  return (
    <article className={styles.metricCard}>
      <span className={styles.metricTitle}>{title}</span>
      <strong className={styles.metricValue}>{value}</strong>
      <span className={`${styles.metricSub} ${styles[`sub_${tone}`]}`}>
        {subIcon}
        {sub}
      </span>
    </article>
  );
}

function formatRelative(iso?: string | null): string {
  if (!iso) return "just now";
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function statusFromFlags(row: { has_test: boolean; has_docs: boolean }): string {
  if (row.has_test && row.has_docs) return "Fully covered";
  if (!row.has_test && !row.has_docs) return "No test, no docs";
  if (!row.has_test) return "No test";
  if (!row.has_docs) return "No docs";
  return "Partial";
}

function labelTone(label: string, status: string): string {
  if (label === "New in PR") return "gray";
  if (label === "Fully covered" || status === "green") return "green";
  if (label === "No test, no docs" || status === "red") return "red";
  return "amber";
}
