import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, FolderGit2, FileCode2, TestTube2, Network, Github } from "lucide-react";
import axios from "axios";
import { specwright, Project, ProjectCreateResponse } from "@/api/specwright";
import styles from "./HomePage.module.css";

type ConnectMode = "local" | "github";

export default function HomePage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [mode, setMode] = useState<ConnectMode>("local");
  const [name, setName] = useState("My API");
  const [path, setPath] = useState("");
  const [pathError, setPathError] = useState("");
  const [githubUrl, setGithubUrl] = useState("https://github.com/tiangolo/fastapi");
  const [localCheckout, setLocalCheckout] = useState("");

  const defaultParentPath =
    typeof window !== "undefined"
      ? "c:\\Software Projects"
      : "";
  const defaultPath =
    typeof window !== "undefined"
      ? "c:\\Software Projects\\Specwright\\api"
      : "";

  function handleConnect() {
    setPathError("");
    if (mode === "local" && !path.trim()) {
      setPathError("Enter the absolute path to your project folder.");
      return;
    }
    create.mutate();
  }

  function apiErrorMessage(err: unknown, fallback: string): string {
    if (axios.isAxiosError(err)) {
      if (err.code === "ECONNABORTED") {
        return "Scan timed out — restart dev (stop-dev.ps1) and try again.";
      }
      if (!err.response) {
        return "Cannot reach Specwright API on port 8088. Run .\\scripts\\stop-dev.ps1 then .\\scripts\\dev.ps1 and wait for API ready.";
      }
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (typeof detail === "string" && detail.trim()) return detail;
      if (status === 500) {
        return "Scan failed on the server (often SQLite busy). Run .\\scripts\\stop-dev.ps1 then .\\scripts\\dev.ps1 and retry.";
      }
      if (status === 400 && typeof detail === "string") return detail;
    }
    return fallback;
  }

  const { data: apiHealth, isError: apiDown } = useQuery({
    queryKey: ["health"],
    queryFn: async () => (await specwright.get("/health")).data,
    retry: 1,
    refetchInterval: 15_000,
  });

  const { data: roadmap } = useQuery({
    queryKey: ["roadmap"],
    queryFn: async () => (await specwright.get("/roadmap")).data as {
      tagline: string;
      frameworks: { name: string; status: string; detail: string }[];
    },
  });

  const { data: projects } = useQuery({
    queryKey: ["projects"],
    queryFn: async () => (await specwright.get<Project[]>("/projects")).data,
  });

  const afterCreate = (p: ProjectCreateResponse) => {
    qc.invalidateQueries({ queryKey: ["projects"] });
    if (p.initial_scan) {
      qc.setQueryData(["scans", p.id], [p.initial_scan]);
    }
    if (p.connected_message) {
      sessionStorage.setItem(`specwright-connect-msg-${p.id}`, p.connected_message);
    }
    navigate(`/project/${p.id}`);
  };

  const createLocal = useMutation({
    mutationFn: async () =>
      (
        await specwright.post<ProjectCreateResponse>("/projects", {
          name,
          root_path: path.trim(),
          framework: "auto",
        })
      ).data,
    onSuccess: afterCreate,
  });

  const createGithub = useMutation({
    mutationFn: async () =>
      (
        await specwright.post<ProjectCreateResponse>("/projects/from-github", {
          github_url: githubUrl,
          name: name || undefined,
          local_path: localCheckout.trim() || undefined,
          prefer_local: true,
        })
      ).data,
    onSuccess: afterCreate,
  });

  const create = mode === "github" ? createGithub : createLocal;

  return (
    <main className={styles.page}>
      <section className={styles.hero}>
        <p className={styles.eyebrow}>The documentation layer for FastAPI teams</p>
        <h1>
          Your API docs stay in sync
          <em> — automatically</em>
        </h1>
        <p className={styles.lead}>
          Specwright reads your code and keeps OpenAPI, tests, and diagrams updated on every save.
          Swagger and Postman need manual input — we don&apos;t.
        </p>
        <div className={styles.pills}>
          <span>
            <FileCode2 size={14} /> OpenAPI 3.1
          </span>
          <span>
            <TestTube2 size={14} /> Pytest scaffold
          </span>
          <span>
            <Network size={14} /> Mermaid ER
          </span>
        </div>
        <p className={styles.quickLinks}>
          <Link to="/try">Try a GitHub repo — no install</Link>
          <span aria-hidden>·</span>
          <Link to="/billing">View pricing</Link>
          <span aria-hidden>·</span>
          <Link to="/api">API reference</Link>
        </p>
      </section>

      <section className={styles.connect}>
        <h2>
          <FolderGit2 size={20} /> Connect a codebase
        </h2>
        {apiDown && (
          <p className={styles.err}>
            API offline — scans will fail until you run .\\scripts\\stop-dev.ps1 then .\\scripts\\dev.ps1
            (wait for &quot;API ready.&quot;).
          </p>
        )}
        {apiHealth && !apiDown && (
          <p className={styles.hint}>API connected — ready to scan.</p>
        )}
        <div className={styles.modeTabs}>
          <button
            type="button"
            className={mode === "github" ? styles.modeActive : ""}
            onClick={() => setMode("github")}
          >
            <Github size={16} /> GitHub URL
          </button>
          <button
            type="button"
            className={mode === "local" ? styles.modeActive : ""}
            onClick={() => setMode("local")}
          >
            <FolderGit2 size={16} /> Local path
          </button>
        </div>
        <div className={styles.form}>
          <input
            placeholder="Project name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          {mode === "github" ? (
            <>
              <input
                placeholder="https://github.com/org/your-api"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
              />
              <input
                placeholder={`Optional: local checkout e.g. ${defaultParentPath}\\Your-Repo`}
                value={localCheckout}
                onChange={(e) => setLocalCheckout(e.target.value)}
              />
            </>
          ) : (
            <input
              placeholder={`e.g. ${defaultParentPath}\\Elite Fintech Systems`}
              value={path}
              onChange={(e) => setPath(e.target.value)}
            />
          )}
          <button
            type="button"
            className={styles.primary}
            disabled={create.isPending}
            onClick={handleConnect}
          >
            {create.isPending
              ? mode === "github"
                ? "Connecting & scanning…"
                : "Scanning…"
              : "Connect & scan"}
            <ArrowRight size={16} />
          </button>
        </div>
        <p className={styles.hint}>
          {mode === "local"
            ? "Scans your folder directly — no clone. Artifacts are written into that project on disk."
            : "GitHub URL links PR comments. Paste a local path in the optional field to scan your checkout (no clone)."}
        </p>
        {pathError && <p className={styles.err}>{pathError}</p>}
        {create.isError && (
          <p className={styles.err}>
            {mode === "github"
              ? apiErrorMessage(
                  create.error,
                  "Could not connect — check GitHub URL, git on PATH, or paste your local checkout path."
                )
              : apiErrorMessage(
                  create.error,
                  "Connect failed — check that dev is running (API on port 8088)."
                )}
          </p>
        )}
      </section>

      {roadmap && (
        <section className={styles.roadmap}>
          <h3>Platform roadmap</h3>
          <ul>
            {roadmap.frameworks.map((f) => (
              <li key={f.name} data-status={f.status}>
                <strong>{f.name}</strong>
                <span>{f.status === "live" ? "Live" : "Planned"}</span>
                <p>{f.detail}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {projects && projects.length > 0 && (
        <section className={styles.teamCta}>
          <p>
            Managing multiple repos?{" "}
            <Link to="/dashboard">Open the team dashboard</Link> for scores, weekly drift,
            and coverage trends.
          </p>
        </section>
      )}

      {projects && projects.length > 0 && (
        <section className={styles.recent}>
          <h3>Recent projects</h3>
          <ul>
            {projects.map((p) => (
              <li key={p.id}>
                <button type="button" onClick={() => navigate(`/project/${p.id}`)}>
                  <strong>{p.name}</strong>
                  <code>{p.root_path}</code>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
