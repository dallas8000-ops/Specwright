import type { MeaningContext, MeaningAction } from "@/types/meaning";
import styles from "./MeaningStrip.module.css";

interface MeaningStripProps {
  meaning: MeaningContext;
  compact?: boolean;
  onAction?: (action: MeaningAction) => void;
}

/** Inline four-question context on list rows — meaning, not raw fields. */
export default function MeaningStrip({ meaning, compact, onAction }: MeaningStripProps) {
  if (compact) {
    return (
      <div className={styles.compact}>
        <p>
          <strong>Why:</strong> {meaning.why_it_matters}
        </p>
        <p className={styles.next}>
          <strong>Next:</strong> {meaning.what_next}
        </p>
      </div>
    );
  }

  return (
    <div className={styles.strip}>
      <dl>
        <div>
          <dt>What</dt>
          <dd>{meaning.what_happened}</dd>
        </div>
        <div>
          <dt>Who</dt>
          <dd>{meaning.who}</dd>
        </div>
        <div>
          <dt>Why</dt>
          <dd>{meaning.why_it_matters}</dd>
        </div>
        <div className={styles.nextCell}>
          <dt>Next</dt>
          <dd>{meaning.what_next}</dd>
        </div>
      </dl>
      {meaning.actions && meaning.actions.length > 0 && (
        <div className={styles.rowActions}>
          {meaning.actions.map((a) => (
            <button
              key={a.label}
              type="button"
              className={a.action === "reject" || a.action === "escalate" ? styles.danger : styles.primary}
              onClick={() => onAction?.(a)}
            >
              {a.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
