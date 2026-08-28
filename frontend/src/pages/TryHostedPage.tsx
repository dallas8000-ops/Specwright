import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { Cloud, Github, LayoutDashboard, Loader2 } from "lucide-react";
import { createProjectFromGitHub, specwright } from "@/api/specwright";
import styles from "./TryHostedPage.module.css";

type Preview = {
  repo: string;
  github_url?: string;
  score: number;
  grade: string;
  message: string;
  routes_found: number;
  files_scanned: number;
  breakdown: {
    documentation_pct: number;
    test_coverage_pct: number;
    freshness_pct: number;
  };
};

export default function TryHostedPage() {
  const navigate = useNavigate();
  const [url, setUrl] = useState("https://github.com/tiangolo/fastapi");

  const preview = useMutation({
    mutationFn: async () =>
      (await specwright.post<Preview>("/hosted/preview", { github_url: url })).data,
  });

  const saveToDashboard = useMutation({
    mutationFn: async () => {
      const repo = preview.data?.repo ?? "";
      const name = repo.split("/").pop() || "GitHub project";
      return (
        await createProjectFromGitHub({
          github_url: preview.data?.github_url ?? url,
          name,
        })
      ).data;
    },
    onSuccess: (project) => {
      navigate(`/project/${project.id}`);
    },
  });

  const result = preview.data;

  return (
    <main className={styles.page}>
      <header className={styles.hero}>
        <p className={styles.eyebrow}>
          <Cloud size={16} /> Hosted preview
        </p>
        <h1>Score any public GitHub repo in ~60 seconds</h1>
        <p className={styles.lead}>
          No clone of Specwright required for this preview — paste a repo URL and we
          shallow-clone, scan, and return your Specwright Score. Add to your team
          dashboard for watch mode, badges, and PR automation.
        </p>
      </header>

      <section className={styles.form}>
        <label>
          <Github size={16} /> GitHub repository URL
        </label>
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/org/your-api"
        />
        <button
          type="button"
          disabled={preview.isPending || !url.trim()}
          onClick={() => preview.mutate()}
        >
          {preview.isPending ? (
            <>
              <Loader2 size={16} className={styles.spin} /> Cloning & scanning…
            </>
          ) : (
            "Get Specwright Score"
          )}
        </button>
        {preview.isError && (
          <p className={styles.err}>
            {(preview.error as { response?: { data?: { detail?: string } } })?.response
              ?.data?.detail ?? "Preview failed — ensure git is installed on the API server."}
          </p>
        )}
      </section>

      {result && (
        <section className={styles.result}>
          <div className={styles.scoreRing} data-grade={result.grade}>
            <span>{result.score}</span>
            <small>/ 100</small>
          </div>
          <div>
            <h2>{result.repo}</h2>
            <p>{result.message}</p>
            <ul className={styles.stats}>
              <li>{result.routes_found} routes</li>
              <li>{result.files_scanned} Python files</li>
              <li>{Math.round(result.breakdown.documentation_pct)}% documented</li>
              <li>{Math.round(result.breakdown.test_coverage_pct)}% test coverage</li>
            </ul>
            <div className={styles.actions}>
              <button
                type="button"
                className={styles.saveBtn}
                disabled={saveToDashboard.isPending}
                onClick={() => saveToDashboard.mutate()}
              >
                {saveToDashboard.isPending ? (
                  <>
                    <Loader2 size={16} className={styles.spin} /> Adding to dashboard…
                  </>
                ) : (
                  <>
                    <LayoutDashboard size={16} /> Add to team dashboard
                  </>
                )}
              </button>
            </div>
            {saveToDashboard.isError && (
              <p className={styles.err}>Could not save project — try again or connect from home.</p>
            )}
            <p className={styles.next}>
              Saves with watch mode, artifact sync, and CI workflow enabled automatically.{" "}
              <Link to="/">Connect another repo</Link>
            </p>
          </div>
        </section>
      )}
    </main>
  );
}
