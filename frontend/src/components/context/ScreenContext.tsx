import { Link } from "react-router-dom";
import type { MeaningContext, MeaningAction } from "@/types/meaning";
import styles from "./ScreenContext.module.css";

interface ScreenContextProps {
  title: string;
  context?: MeaningContext | null;
  loading?: boolean;
  onAction?: (action: MeaningAction) => void;
}

export default function ScreenContext({ title, context, loading, onAction }: ScreenContextProps) {
  if (loading) {
    return (
      <section className={styles.frame} aria-busy="true">
        <p className={styles.loading}>Loading context…</p>
      </section>
    );
  }
  if (!context) return null;

  return (
    <section className={styles.frame} aria-label="Situation context">
      <header className={styles.titleRow}>
        <h2>{title}</h2>
        <span className={styles.badge}>Context</span>
      </header>
      <div className={styles.grid}>
        <ContextCell label="What happened" value={context.what_happened} />
        <ContextCell label="Who" value={context.who} />
        <ContextCell label="Why it matters" value={context.why_it_matters} highlight />
        <ContextCell label="What to do next" value={context.what_next} accent />
      </div>
      {context.actions && context.actions.length > 0 && (
        <footer className={styles.actions}>
          {context.actions.map((a) =>
            a.href ? (
              <Link key={a.label} to={a.href} className={styles.actionBtn}>
                {a.label}
              </Link>
            ) : (
              <button
                key={a.label}
                type="button"
                className={styles.actionBtn}
                onClick={() => onAction?.(a)}
              >
                {a.label}
              </button>
            )
          )}
        </footer>
      )}
    </section>
  );
}

function ContextCell({
  label,
  value,
  highlight,
  accent,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  accent?: boolean;
}) {
  return (
    <article
      className={`${styles.cell} ${highlight ? styles.highlight : ""} ${accent ? styles.accent : ""}`}
    >
      <h3>{label}</h3>
      <p>{value}</p>
    </article>
  );
}
