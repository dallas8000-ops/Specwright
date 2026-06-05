"""Hosted-style preview: clone a public GitHub repo and compute score (no local install)."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

from api.analyzers.discovery import collect_python_files, detect_framework
from api.analyzers.fastapi_scanner import analyze_fastapi, collect_routes
from api.analyzers.test_scaffold import generate_tests
from api.services.health_score import build_project_health


_GITHUB_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?(?:#.*)?$",
    re.I,
)


def parse_github_url(url: str) -> tuple[str, str]:
    url = url.strip()
    m = _GITHUB_RE.match(url)
    if not m:
        raise ValueError("Use a public GitHub URL like https://github.com/org/repo")
    owner, repo = m.group(1), m.group(2)
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def _clone_repo(owner: str, repo: str, dest: Path) -> None:
    clone_url = f"https://github.com/{owner}/{repo}.git"
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", "--single-branch", clone_url, str(dest)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "clone failed").strip()[:300]
        raise RuntimeError(f"Could not clone repository: {err}")


def _artifact(kind: str, content: str) -> SimpleNamespace:
    return SimpleNamespace(kind=kind, content=content)


def preview_github_repository(url: str) -> dict:
    owner, repo = parse_github_url(url)
    tmp = Path(tempfile.mkdtemp(prefix="specwright-preview-"))
    try:
        _clone_repo(owner, repo, tmp)
        files = collect_python_files(tmp)
        if not files:
            raise ValueError("No Python files found in repository root.")

        framework = detect_framework(tmp)
        routes = collect_routes(files, tmp)
        openapi, api_md = analyze_fastapi(files, tmp)
        tests = generate_tests(
            framework=framework,
            routes=routes,
            models=[],
            project_name=repo,
        )
        artifacts = [
            _artifact("openapi", openapi),
            _artifact("api_docs", api_md),
            _artifact("tests", tests),
            _artifact("django_docs", ""),
        ]
        health = build_project_health(tmp, artifacts, None)
        score = health["score"]["score"]

        return {
            "github_url": f"https://github.com/{owner}/{repo}",
            "repo": f"{owner}/{repo}",
            "framework": framework,
            "routes_found": len(routes),
            "files_scanned": len(files),
            "score": score,
            "grade": health["score"]["grade"],
            "summary": health["score"]["summary"],
            "breakdown": health["score"]["breakdown"],
            "drift": health["drift"],
            "hosted": True,
            "message": (
                f"Scanned {len(files)} files · {len(routes)} routes · "
                f"Specwright Score {score}/100"
            ),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
