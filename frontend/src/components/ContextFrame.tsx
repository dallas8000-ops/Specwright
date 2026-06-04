import styles from "./ContextFrame.module.css";

interface Props {
  what: string;
  who: string;
  why: string;
  next: string;
}

export default function ContextFrame({ what, who, why, next }: Props) {
  return (
    <section className={styles.frame}>
      <div className={styles.cell}>
        <span>What happened</span>
        <p>{what}</p>
      </div>
      <div className={styles.cell}>
        <span>Who</span>
        <p>{who}</p>
      </div>
      <div className={`${styles.cell} ${styles.why}`}>
        <span>Why it matters</span>
        <p>{why}</p>
      </div>
      <div className={`${styles.cell} ${styles.next}`}>
        <span>What to do next</span>
        <p>{next}</p>
      </div>
    </section>
  );
}
