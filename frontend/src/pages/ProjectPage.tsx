import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Play,
  Download,
  Copy,
  Check,
  FileText,
  Braces,
  GitBranch,
  TestTube,
} from "lucide-react";
import {
  specwright,
  Project,
  Scan,
  Artifact,
  Context,
  fillDescriptions,
} from "@/api/specwright";
import ContextFrame from "@/components/ContextFrame";
import ArtifactViewer from "@/components/ArtifactViewer";
import ProjectIntegrations from "@/components/ProjectIntegrations";
import ProjectAITools from "@/components/ProjectAITools";
import HealthDashboard from "@/components/HealthDashboard";
import styles from "./ProjectPage.module.css";

const KIND_ICON: Record<string, typeof FileText> = {
  openapi: Braces,
  api_docs: FileText,
  django_diagram: GitBranch,
  django_docs: FileText,
  tests: TestTube,
  readme: FileText,
};

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const qc = useQueryClient();
  const [selected, setSelected] = useState<Artifact | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: async () => (await specwright.get<Project>(`/projects/${projectId}`)).data,
  });

  const { data: context } = useQuery({
    queryKey: ["context", projectId],
    queryFn: async () => (await specwright.get<Context>(`/projects/${projectId}/context`)).data,
  });

  const { data: scans } = useQuery({
    queryKey: ["scans", projectId],
    queryFn: async () => (await specwright.get<Scan[]>(`/projects/${projectId}/scans`)).data,
  });

  const scan = useMutation({
    mutationFn: async () => (await specwright.post<Scan>(`/projects/${projectId}/scan`)).data,
    onSuccess: (s) => {
      qc.invalidateQueries({ queryKey: ["scans", projectId] });
      qc.invalidateQueries({ queryKey: ["context", projectId] });
      qc.invalidateQueries({ queryKey: ["health", projectId] });
      qc.invalidateQueries({ queryKey: ["ai-suite", projectId] });
      if (s.artifacts[0]) setSelected(s.artifacts[0]);
    },
  });

  const fillDocs = useMutation({
    mutationFn: async () => (await fillDescriptions(projectId)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["scans", projectId] });
      qc.invalidateQueries({ queryKey: ["health", projectId] });
      qc.invalidateQueries({ queryKey: ["ai-suite", projectId] });
    },
  });

  const latest = scans?.[0];
  const artifacts = latest?.artifacts ?? [];

  function copyContent() {
    if (!selected) return;
    navigator.clipboard.writeText(selected.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function downloadContent() {
    if (!selected) return;
    const blob = new Blob([selected.content], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = selected.file_path.split("/").pop() || "artifact.txt";
    a.click();
  }

  return (
    <main className={styles.page}>
      <div className={styles.top}>
        <nav className={styles.crumb} aria-label="Breadcrumb">
          <Link to="/">Projects</Link>
          <span aria-hidden>/</span>
          <span className={styles.crumbCurrent}>{project?.name ?? "Project"}</span>
        </nav>
        <div className={styles.titleRow}>
          <code className={styles.rootPath}>{project?.root_path}</code>
          <button
            type="button"
            className={styles.scanBtn}
            onClick={() => scan.mutate()}
            disabled={scan.isPending}
          >
            <Play size={16} />
            {scan.isPending ? "Scanning codebase…" : "Generate artifacts"}
          </button>
        </div>
      </div>

      {!latest && context && (
        <ContextFrame
          what={context.what_happened}
          who={context.who}
          why={context.why_it_matters}
          next={context.what_next}
        />
      )}

      {scan.isPending && (
        <div className={styles.progress}>
          <div className={styles.bar} />
          <p>Parsing Python · discovering routes · building OpenAPI & tests…</p>
        </div>
      )}

      {latest && (
        <HealthDashboard
          projectId={projectId}
          projectName={project?.name}
          framework={project?.framework ?? "api"}
          lastScannedAt={latest.created_at}
          onGenerate={() => scan.mutate()}
          isGenerating={scan.isPending}
          onFillDescriptions={
            project?.plan === "pro" || project?.plan === "enterprise"
              ? () => fillDocs.mutate()
              : undefined
          }
          isFillingDescriptions={fillDocs.isPending}
        />
      )}

      <ProjectAITools
        projectId={projectId}
        project={project}
        onArtifactsUpdated={() => {
          qc.invalidateQueries({ queryKey: ["scans", projectId] });
          qc.invalidateQueries({ queryKey: ["health", projectId] });
          qc.invalidateQueries({ queryKey: ["ai-suite", projectId] });
        }}
        onTestsUpdated={(content) => {
          const testArt = artifacts.find((a) => a.kind === "tests");
          if (testArt && selected?.id === testArt.id) {
            setSelected({ ...testArt, content });
          }
        }}
      />

      <ProjectIntegrations
        projectId={projectId}
        project={project}
        selectedArtifactId={selected?.id ?? null}
        onScanTriggered={() => {
          qc.invalidateQueries({ queryKey: ["scans", projectId] });
          qc.invalidateQueries({ queryKey: ["ai-suite", projectId] });
        }}
        onArtifactPolished={(content) =>
          setSelected((s) => (s ? { ...s, content, polished: true } : null))
        }
      />

      <div className={styles.workspace}>
        <aside className={styles.sidebar}>
          <h3>Generated artifacts</h3>
          {artifacts.length === 0 && !scan.isPending && (
            <p className={styles.empty}>Run a scan to populate this panel.</p>
          )}
          <ul>
            {artifacts.map((a) => {
              const Icon = KIND_ICON[a.kind] ?? FileText;
              return (
                <li key={a.id}>
                  <button
                    type="button"
                    className={selected?.id === a.id ? styles.active : ""}
                    onClick={() => setSelected(a)}
                  >
                    <Icon size={16} />
                    <div>
                      <strong>{a.title}</strong>
                      <span>{a.file_path}</span>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>

        <section className={styles.viewer}>
          {selected ? (
            <>
              <header>
                <h2>{selected.title}</h2>
                <div className={styles.actions}>
                  <button type="button" onClick={copyContent}>
                    {copied ? <Check size={14} /> : <Copy size={14} />}
                    {copied ? "Copied" : "Copy"}
                  </button>
                  <button type="button" onClick={downloadContent}>
                    <Download size={14} /> Export
                  </button>
                </div>
              </header>
              <ArtifactViewer artifact={selected} />
            </>
          ) : (
            <div className={styles.placeholder}>
              <p>Select an artifact or run Generate artifacts</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
