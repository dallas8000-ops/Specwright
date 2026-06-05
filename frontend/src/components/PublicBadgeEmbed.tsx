import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Award, Check, Copy } from "lucide-react";
import { fetchBadgeEmbed } from "@/api/specwright";
import styles from "./PublicBadgeEmbed.module.css";

type Props = { projectId: number };

export default function PublicBadgeEmbed({ projectId }: Props) {
  const [copied, setCopied] = useState(false);

  const { data: embed } = useQuery({
    queryKey: ["badge-embed", projectId],
    queryFn: () => fetchBadgeEmbed(projectId),
  });

  if (!embed) return null;

  function copyMarkdown() {
    navigator.clipboard.writeText(embed!.markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <section className={styles.panel}>
      <div className={styles.head}>
        <Award size={18} />
        <div>
          <h3>README score badge</h3>
          <p>Embed in your repo — visitors see your Specwright Score and discover Specwright.</p>
        </div>
      </div>
      {embed.score != null && (
        <a
          href={embed.project_url}
          target="_blank"
          rel="noreferrer"
          className={styles.preview}
        >
          <img src={embed.image_url} alt={`Specwright Score ${embed.score}`} />
        </a>
      )}
      <pre className={styles.code}>{embed.markdown}</pre>
      <button type="button" className={styles.copyBtn} onClick={copyMarkdown}>
        {copied ? <Check size={14} /> : <Copy size={14} />}
        {copied ? "Copied" : "Copy markdown"}
      </button>
      <p className={styles.hint}>
        Self-hosted: <code>{embed.image_url}</code>
        <br />
        When hosted: <code>{embed.hosted_image_url}</code>
      </p>
    </section>
  );
}
