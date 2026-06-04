import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BookOpen,
  GitPullRequest,
  Loader2,
  MessageCircle,
  Sparkles,
  TestTube2,
} from "lucide-react";
import { specwright, Features, Project } from "@/api/specwright";
import styles from "./ProjectIntegrations.module.css";

type Props = {
  projectId: number;
  project: Project | undefined;
  onArtifactsUpdated: () => void;
  onTestsUpdated?: (content: string) => void;
};

export default function ProjectAITools({
  projectId,
  project,
  onArtifactsUpdated,
  onTestsUpdated,
}: Props) {
  const [question, setQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState("");
  const [migrationNote, setMigrationNote] = useState("");

  const { data: features } = useQuery({
    queryKey: ["features"],
    queryFn: async () => (await specwright.get<Features>("/features")).data,
  });

  const { data: suite } = useQuery({
    queryKey: ["ai-suite", projectId],
    queryFn: async () => (await specwright.get(`/projects/${projectId}/ai/suite`)).data,
  });

  const canAi =
    features?.ai_suite &&
    (project?.plan === "pro" || project?.plan === "enterprise");

  const descriptions = useMutation({
    mutationFn: async () =>
      (await specwright.post(`/projects/${projectId}/ai/descriptions`)).data,
    onSuccess: () => onArtifactsUpdated(),
  });

  const tests = useMutation({
    mutationFn: async () =>
      (await specwright.post(`/projects/${projectId}/ai/tests`)).data as {
        content: string;
        enhanced: number;
      },
    onSuccess: (data) => {
      onArtifactsUpdated();
      onTestsUpdated?.(data.content);
    },
  });

  const migration = useMutation({
    mutationFn: async () =>
      (await specwright.post(`/projects/${projectId}/ai/migration-note`)).data as {
        note: string;
      },
    onSuccess: (data) => setMigrationNote(data.note),
  });

  const chat = useMutation({
    mutationFn: async () =>
      (
        await specwright.post(`/projects/${projectId}/ai/chat`, {
          question,
        })
      ).data as { answer: string },
    onSuccess: (data) => setChatAnswer(data.answer),
  });

  return (
    <section className={styles.panel}>
      <h3>
        <Sparkles size={18} /> Grounded AI
      </h3>
      <p className={styles.suiteIntro}>
        AST owns truth; AI owns prose. Only routes from your last scan are used — no invented
        endpoints.
      </p>

      {suite && (
        <div className={styles.suiteStats}>
          <span>{suite.description_gaps} description gaps</span>
          <span>{suite.docstring_mismatches} docstring mismatches</span>
          <span>{suite.breaking_change?.breaking_count ?? 0} breaking changes</span>
        </div>
      )}

      <div className={styles.grid}>
        <div className={styles.card}>
          <div className={styles.cardHead}>
            <BookOpen size={16} />
            <strong>Fill descriptions</strong>
          </div>
          <p>Improve weak OpenAPI summaries from handler docstrings.</p>
          <button
            type="button"
            disabled={!canAi || descriptions.isPending}
            onClick={() => descriptions.mutate()}
          >
            {descriptions.isPending ? <Loader2 size={14} className={styles.spin} /> : null}
            Fill gaps
          </button>
          {descriptions.isSuccess && (
            <span className={styles.status}>
              Updated {descriptions.data.filled} operation(s)
            </span>
          )}
        </div>

        <div className={styles.card}>
          <div className={styles.cardHead}>
            <TestTube2 size={16} />
            <strong>Test bodies</strong>
          </div>
          <p>Replace smoke stubs with grounded pytest bodies.</p>
          <button
            type="button"
            disabled={!canAi || tests.isPending}
            onClick={() => tests.mutate()}
          >
            {tests.isPending ? <Loader2 size={14} className={styles.spin} /> : null}
            Enhance tests
          </button>
          {tests.isSuccess && (
            <span className={styles.status}>
              Enhanced {tests.data.enhanced} test(s)
            </span>
          )}
        </div>

        <div className={styles.card}>
          <div className={styles.cardHead}>
            <GitPullRequest size={16} />
            <strong>Migration note</strong>
          </div>
          <p>Client-facing paragraph from PR diff + score (also on GitHub comments).</p>
          <button
            type="button"
            disabled={!canAi || migration.isPending}
            onClick={() => migration.mutate()}
          >
            {migration.isPending ? <Loader2 size={14} className={styles.spin} /> : null}
            Generate note
          </button>
          {migrationNote && <pre className={styles.notePreview}>{migrationNote}</pre>}
        </div>

        <div className={styles.card}>
          <div className={styles.cardHead}>
            <AlertTriangle size={16} />
            <strong>Breaking changes</strong>
          </div>
          <p>Rule-based triage of added vs removed paths (free with any scan).</p>
          {suite?.breaking_change?.items?.length ? (
            <ul className={styles.triageList}>
              {suite.breaking_change.items.slice(0, 5).map((item) => (
                <li key={`${item.change}-${item.path}`}>
                  <span data-class={item.classification}>{item.classification}</span>{" "}
                  <code>{item.path}</code>
                </li>
              ))}
            </ul>
          ) : (
            <span className={styles.hint}>No path changes in latest scan</span>
          )}
        </div>

        <div className={`${styles.card} ${styles.cardWide}`}>
          <div className={styles.cardHead}>
            <MessageCircle size={16} />
            <strong>How do I…?</strong>
          </div>
          <input
            placeholder="e.g. How do I list projects?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button
            type="button"
            disabled={!canAi || !question.trim() || chat.isPending}
            onClick={() => chat.mutate()}
          >
            {chat.isPending ? <Loader2 size={14} className={styles.spin} /> : null}
            Ask (scoped to scan)
          </button>
          {chatAnswer && <pre className={styles.notePreview}>{chatAnswer}</pre>}
        </div>
      </div>

      {!features?.ai_suite && (
        <span className={styles.hint}>Set SPECWRIGHT_AI_API_KEY on the API server</span>
      )}
      {features?.ai_suite && project?.plan === "starter" && (
        <span className={styles.hint}>Upgrade to Pro for LLM-powered AI actions</span>
      )}
    </section>
  );
}
