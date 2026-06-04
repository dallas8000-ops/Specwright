import { useState } from "react";
import { Radio, ChevronDown, ChevronUp } from "lucide-react";
import { useRealtimeStore } from "@/stores/realtime";
import styles from "./LiveFeed.module.css";

const SERVICE_LABEL: Record<string, string> = {
  case_service: "Case",
  approval_service: "Sign-off",
  execution_service: "Execution",
  intelligence_service: "Intelligence",
};

export default function LiveFeed() {
  const [open, setOpen] = useState(false);
  const status = useRealtimeStore((s) => s.status);
  const feed = useRealtimeStore((s) => s.feed);

  if (status === "disconnected" && feed.length === 0) return null;

  return (
    <div className={styles.panel}>
      <button type="button" className={styles.toggle} onClick={() => setOpen(!open)}>
        <Radio size={14} className={status === "connected" ? styles.live : styles.offline} />
        <span>Live stream</span>
        <span className={styles.status}>{status}</span>
        {open ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
      </button>
      {open && (
        <ul className={styles.list}>
          {feed.length === 0 && <li className={styles.empty}>Waiting for domain events…</li>}
          {feed.map((e) => (
            <li key={`${e.id}-${e.created_at}`}>
              <span className={styles.svc}>{SERVICE_LABEL[e.service] ?? e.service}</span>
              <span className={styles.ev}>{e.event_type}</span>
              <time>{new Date(e.created_at).toLocaleTimeString()}</time>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
