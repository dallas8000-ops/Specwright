import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  BookOpen,
  GitPullRequest,
  Loader2,
  MessageCircle,
  Sparkles,
  TestTube2,
} from "lucide-react";
import {
  activateMockPro,
  specwright,
  Features,
  Project,
} from "@/api/specwright";
import styles from "./ProjectIntegrations.module.css";

type Props = {
  projectId: number;
  project: Project | undefined;
  hasScan: boolean;
  onArtifactsUpdated: () => void;
  onTestsUpdated?: (content: string) => void;
};

export default function ProjectAITools({
  projectId,
  project,
  hasScan,
  onArtifactsUpdated,
  onTestsUpdated,
}: Props) {
  const qc = useQueryClient();
  const proUpgradeStarted = useRef(false);
  const [question, setQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState("");
  const [migrationNote, setMigrationNote] = useState("");

  const { data: features } = useQuery({
    queryKey: ["features"],
    queryFn: async () => (await specwright.get<Features>("/features")).data,
  });

  const { data: suite, isError: suiteError } = useQuery({
    queryKey: ["ai-suite", projectId],
    queryFn: async () => (await specwright.get(`/projects/${projectId}/ai/suite`)).data,
    enabled: hasScan,
  });

  const upgradePro = useMutation({
    mutationFn: () => activateMockPro(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project", projectId] });
      qc.invalidateQueries({ queryKey: ["billing"] });
    },
  });

  useEffect(() => {
    if (
      features?.billing_mock &&
      project?.plan === "starter" &&
      !proUpgradeStarted.current &&
      !upgradePro.isPending
    ) {
      proUpgradeStarted.current = true;
      upgradePro.mutate();
    }
  }, [features?.billing_mock, project?.plan, upgradePro]);

  const isPro = project?.plan === "pro" || project?.plan === "enterprise";
  const canAi = Boolean(features?.ai_suite && isPro);

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

  if (!hasScan || suiteError) {
    return null;
  }

  const breakingItems = suite?.breaking_change?.items ?? [];
  const hasBreaking = breakingItems.length > 0;

  return (
    <section className={styles.panel}>
      <h3>
        <Sparkles size={18} /> Grounded AI
      </h3>
      <p className={styles.suiteIntro}>
        AST owns truth; AI owns prose. Scan insights below are always live; LLM actions
        use routes from your last scan only.
      </p>

      {suite && (
        <div className={styles.suiteStats}>
          <span>{suite.description_gaps} description gaps</span>
          <span>{suite.docstring_mismatches} docstring mismatches</span>
          <span>{suite.breaking_change?.breaking_count ?? 0} breaking changes</span>
        </div>
      )}

      {canAi ? (
        <div className={styles.grid}>
          <div className={styles.card}>
            <div className={styles.cardHead}>
              <BookOpen size={16} />
              <strong>Fill descriptions</strong>
            </div>
            <p>Improve weak OpenAPI summaries from handler docstrings.</p>
            <button
              type="button"
              disabled={descriptions.isPending}
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
              disabled={tests.isPending}
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
              disabled={migration.isPending}
              onClick={() => migration.mutate()}
            >
              {migration.isPending ? <Loader2 size={14} className={styles.spin} /> : null}
              Generate note
            </button>
            {migrationNote && <pre className={styles.notePreview}>{migrationNote}</pre>}
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
              disabled={!question.trim() || chat.isPending}
              onClick={() => chat.mutate()}
            >
              {chat.isPending ? <Loader2 size={14} className={styles.spin} /> : null}
              Ask (scoped to scan)
            </button>
            {chatAnswer && <pre className={styles.notePreview}>{chatAnswer}</pre>}
          </div>
        </div>
      ) : (
        <p className={styles.capabilityNote}>
          {!features?.ai_suite
            ? "LLM actions: add SPECWRIGHT_AI_API_KEY to .env and restart the API."
            : !isPro
              ? "LLM actions: Pro plan required (use Billing or dev mock checkout)."
              : "LLM actions: waiting for API configuration."}
        </p>
      )}

      {hasBreaking && (
        <div className={styles.breakingSection}>
          <h4>
            <AlertTriangle size={16} /> Route changes detected
          </h4>
          <ul className={styles.triageList}>
            {breakingItems.slice(0, 8).map((item: { change: string; path: string; classification: string }) => (
              <li key={`${item.change}-${item.path}`}>
                <span data-class={item.classification}>{item.classification}</span>{" "}
                <code>{item.path}</code>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
