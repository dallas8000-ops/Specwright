import type { Artifact } from "@/api/specwright";
import styles from "./ArtifactViewer.module.css";

type Props = {
  artifact: Artifact;
};

function isMermaid(kind: string, content: string) {
  return (
    kind === "django_diagram" ||
    content.trimStart().startsWith("erDiagram") ||
    content.trimStart().startsWith("flowchart")
  );
}

function isMarkdown(kind: string, filePath: string) {
  return (
    kind === "api_docs" ||
    kind === "django_docs" ||
    kind === "readme" ||
    filePath.endsWith(".md")
  );
}

export default function ArtifactViewer({ artifact }: Props) {
  if (isMermaid(artifact.kind, artifact.content)) {
    const empty =
      artifact.content.includes("PLACEHOLDER") ||
      artifact.content.includes("No models");
    return (
      <div className={styles.viewer}>
        {empty ? (
          <p className={styles.hint}>
            No Django models in this codebase. Point Specwright at a project with{" "}
            <code>models.py</code> for an ER diagram.
          </p>
        ) : (
          <p className={styles.hint}>
            Mermaid diagram — paste into{" "}
            <a href="https://mermaid.live" target="_blank" rel="noreferrer">
              mermaid.live
            </a>{" "}
            or your docs.
          </p>
        )}
        <pre className={styles.code}>{artifact.content}</pre>
      </div>
    );
  }

  if (isMarkdown(artifact.kind, artifact.file_path)) {
    return (
      <div className={styles.viewer}>
        <article
          className={styles.markdown}
          dangerouslySetInnerHTML={{ __html: simpleMarkdown(artifact.content) }}
        />
        <details className={styles.source}>
          <summary>View raw markdown</summary>
          <pre>{artifact.content}</pre>
        </details>
      </div>
    );
  }

  return <pre className={styles.code}>{artifact.content}</pre>;
}

function simpleMarkdown(md: string): string {
  return md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/^\|(.+)\|$/gm, (row) => {
      const cells = row.split("|").filter(Boolean);
      if (cells.every((c) => /^[-:]+$/.test(c.trim()))) return "";
      return `<tr>${cells.map((c) => `<td>${c.trim()}</td>`).join("")}</tr>`;
    })
    .replace(/(<tr>[\s\S]*?<\/tr>\n?)+/g, (block) => `<table>${block}</table>`)
    .replace(/\n\n/g, "</p><p>")
    .replace(/^/, "<p>")
    .concat("</p>");
}
