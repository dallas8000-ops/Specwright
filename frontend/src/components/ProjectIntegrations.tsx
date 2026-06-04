import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, Github, Sparkles, Loader2, Workflow, BookOpen, Bell } from "lucide-react";
import {
  specwright,
  Features,
  Project,
  postPrComment,
  polishArtifact,
  updateProject,
  fetchCiTemplate,
  pushNotion,
  setSlackWebhook,
} from "@/api/specwright";
import styles from "./ProjectIntegrations.module.css";

type Props = {
  projectId: number;
  project: Project | undefined;
  selectedArtifactId: number | null;
  onScanTriggered: () => void;
  onArtifactPolished?: (content: string) => void;
};

export default function ProjectIntegrations({
  projectId,
  project,
  selectedArtifactId,
  onScanTriggered,
  onArtifactPolished,
}: Props) {
  const qc = useQueryClient();
  const [prNumber, setPrNumber] = useState("");
  const [githubRepo, setGithubRepo] = useState(project?.github_repo ?? "");
  const [watchStatus, setWatchStatus] = useState("");
  const [slackUrl, setSlackUrl] = useState("");

  const { data: features } = useQuery({
    queryKey: ["features"],
    queryFn: async () => (await specwright.get<Features>("/features")).data,
  });

  useEffect(() => {
    setGithubRepo(project?.github_repo ?? "");
  }, [project?.github_repo]);

  useEffect(() => {
    if (!project?.watch_enabled) return;

    const es = new EventSource(`/api/v1/projects/${projectId}/watch/events`);
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === "scan_completed") {
          setWatchStatus(`Watch: regenerated (${data.artifact_count} artifacts)`);
          qc.invalidateQueries({ queryKey: ["scans", projectId] });
          qc.invalidateQueries({ queryKey: ["context", projectId] });
          qc.invalidateQueries({ queryKey: ["health", projectId] });
          onScanTriggered();
        } else if (data.type === "scan_started") {
          setWatchStatus("Watch: scanning…");
        } else if (data.type === "scan_failed") {
          setWatchStatus(`Watch failed: ${data.error}`);
        }
      } catch {
        /* ignore */
      }
    };
    return () => es.close();
  }, [project?.watch_enabled, projectId, qc, onScanTriggered]);

  const watchToggle = useMutation({
    mutationFn: async (enabled: boolean) =>
      (await updateProject(projectId, { watch_enabled: enabled })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project", projectId] });
      setWatchStatus("");
    },
  });

  const saveRepo = useMutation({
    mutationFn: async () =>
      (await updateProject(projectId, { github_repo: githubRepo })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["project", projectId] }),
  });

  const prComment = useMutation({
    mutationFn: async () =>
      postPrComment(projectId, {
        pr_number: Number(prNumber),
        github_repo: githubRepo || undefined,
      }),
  });

  const polish = useMutation({
    mutationFn: async () => polishArtifact(projectId, selectedArtifactId!),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["scans", projectId] });
      onArtifactPolished?.(res.data.content);
    },
  });

  const canPolish =
    selectedArtifactId != null &&
    (features?.ai_polish || project?.plan === "pro" || project?.plan === "enterprise");

  return (
    <section className={styles.panel}>
      <h3>Integrations</h3>
      <div className={styles.grid}>
        <div className={styles.card}>
          <div className={styles.cardHead}>
            <Eye size={16} />
            <strong>Watch mode</strong>
          </div>
          <p>
            Live sync — every save updates OpenAPI, tests, and docs on disk. No regenerate
            click.
          </p>
          <label className={styles.toggle}>
            <input
              type="checkbox"
              checked={project?.watch_enabled ?? false}
              disabled={watchToggle.isPending}
              onChange={(e) => watchToggle.mutate(e.target.checked)}
            />
            {project?.watch_enabled ? "Watching" : "Off"}
          </label>
          {watchStatus && <span className={styles.status}>{watchStatus}</span>}
        </div>

        <div className={styles.card}>
          <div className={styles.cardHead}>
            <Github size={16} />
            <strong>GitHub PR comment</strong>
          </div>
          <input
            placeholder="owner/repo"
            value={githubRepo}
            onChange={(e) => setGithubRepo(e.target.value)}
            onBlur={() => saveRepo.mutate()}
          />
          <input
            placeholder="PR number"
            value={prNumber}
            onChange={(e) => setPrNumber(e.target.value)}
          />
          <button
            type="button"
            disabled={!prNumber || prComment.isPending || !features?.github}
            onClick={() => prComment.mutate()}
            title={
              features?.github
                ? "Post scan summary to PR"
                : "Set SPECWRIGHT_GITHUB_TOKEN on API"
            }
          >
            {prComment.isPending ? <Loader2 size={14} className={styles.spin} /> : null}
            Comment on PR
          </button>
          {prComment.isSuccess && (
            <a href={prComment.data.html_url} target="_blank" rel="noreferrer">
              View comment
            </a>
          )}
        </div>

        <div className={styles.card}>
          <div className={styles.cardHead}>
            <Sparkles size={16} />
            <strong>AI polish</strong>
          </div>
          <p>Improve markdown artifacts (API docs, model docs).</p>
          <button
            type="button"
            disabled={!canPolish || polish.isPending}
            onClick={() => polish.mutate()}
          >
            {polish.isPending ? <Loader2 size={14} className={styles.spin} /> : null}
            Polish selected
          </button>
          {!features?.ai_polish && (
            <span className={styles.hint}>Add SPECWRIGHT_AI_API_KEY on API</span>
          )}
        </div>

        <div className={styles.card}>
          <div className={styles.cardHead}>
            <Workflow size={16} />
            <strong>CI integration</strong>
          </div>
          <p>GitHub Action — fail build if OpenAPI drifts from code.</p>
          <button
            type="button"
            onClick={async () => {
              const { data } = await fetchCiTemplate(projectId);
              const blob = new Blob([data.content], { type: "text/yaml" });
              const a = document.createElement("a");
              a.href = URL.createObjectURL(blob);
              a.download = data.filename.replace(/^.*[/\\]/, "");
              a.click();
            }}
          >
            Download specwright.yml
          </button>
        </div>

        <div className={styles.card}>
          <div className={styles.cardHead}>
            <BookOpen size={16} />
            <strong>Push to Notion</strong>
          </div>
          <p>Export API reference to your team workspace.</p>
          <button
            type="button"
            onClick={() => pushNotion(projectId, { title: `${project?.name} API` })}
          >
            Push API docs
          </button>
        </div>

        <div className={styles.card}>
          <div className={styles.cardHead}>
            <Bell size={16} />
            <strong>Drift alerts</strong>
          </div>
          <p>Slack when spec falls behind codebase.</p>
          <input
            placeholder="Slack webhook URL"
            value={slackUrl}
            onChange={(e) => setSlackUrl(e.target.value)}
            onBlur={() => slackUrl && setSlackWebhook(projectId, slackUrl)}
          />
        </div>
      </div>
    </section>
  );
}
