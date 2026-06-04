import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, FolderGit2, FileCode2, TestTube2, Network } from "lucide-react";
import { specwright, Project } from "@/api/specwright";
import styles from "./HomePage.module.css";

export default function HomePage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [name, setName] = useState("My API");
  const [path, setPath] = useState("");

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

  const create = useMutation({
    mutationFn: async () =>
      (
        await specwright.post<Project>("/projects", {
          name,
          root_path: path,
          framework: "auto",
        })
      ).data,
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      navigate(`/project/${p.id}`);
    },
  });

  const defaultPath =
    typeof window !== "undefined"
      ? "c:\\Software Projects\\AutomationFlow\\api"
      : "";

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
          <Link to="/billing">View pricing</Link>
          <span aria-hidden>·</span>
          <Link to="/api">API reference</Link>
        </p>
      </section>

      <section className={styles.connect}>
        <h2>
          <FolderGit2 size={20} /> Connect a codebase
        </h2>
        <div className={styles.form}>
          <input
            placeholder="Project name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            placeholder={`Absolute path e.g. ${defaultPath}`}
            value={path || defaultPath}
            onChange={(e) => setPath(e.target.value)}
          />
          <button
            type="button"
            className={styles.primary}
            disabled={create.isPending}
            onClick={() => create.mutate()}
          >
            {create.isPending ? "Connecting…" : "Analyze codebase"}
            <ArrowRight size={16} />
          </button>
        </div>
        {create.isError && (
          <p className={styles.err}>Could not access path — use an absolute folder path on disk.</p>
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
