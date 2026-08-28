"""Clone or refresh GitHub repos into a persistent Specwright cache."""
from __future__ import annotations

import subprocess
from pathlib import Path

from api.core.config import settings
from api.services.github_hosted import _clone_repo, parse_github_url


def persistent_repo_path(owner: str, repo: str) -> Path:
    return settings.workspace_root / ".specwright" / "repos" / owner / repo


def _git_pull(dest: Path) -> None:
    proc = subprocess.run(
        ["git", "pull", "--ff-only"],
        cwd=str(dest),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "pull failed").strip()[:300]
        raise RuntimeError(f"Could not update repository: {err}")


def clone_or_update_github_repo(url: str) -> tuple[Path, str, str]:
    """Return local path, owner, repo — clone on first use, pull on repeat."""
    owner, repo = parse_github_url(url)
    dest = persistent_repo_path(owner, repo)
    if dest.exists() and (dest / ".git").exists():
        _git_pull(dest)
    else:
        if dest.exists():
            import shutil

            shutil.rmtree(dest, ignore_errors=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        _clone_repo(owner, repo, dest)
    return dest.resolve(), owner, repo
