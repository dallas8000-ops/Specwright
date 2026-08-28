"""Prefer an existing local git checkout over cloning when connecting via GitHub URL."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from api.core.config import settings
from api.services.github_clone import clone_or_update_github_repo, persistent_repo_path
from api.services.github_hosted import parse_github_url


def _git_origin_url(path: Path) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(path), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _remote_matches_github(url: str, owner: str, repo: str) -> bool:
    normalized = url.strip().lower().removesuffix(".git")
    slug = f"{owner.lower()}/{repo.lower()}"
    return slug in normalized and "github.com" in normalized


_GITHUB_ORIGIN_RE = re.compile(
    r"github\.com[/:]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$",
    re.I,
)


def infer_github_repo(path: Path) -> str:
    """Read git origin and return owner/repo, or empty string."""
    origin = _git_origin_url(path)
    if not origin:
        return ""
    m = _GITHUB_ORIGIN_RE.search(origin.strip())
    if not m:
        return ""
    repo = m.group(2)
    if repo.endswith(".git"):
        repo = repo[:-4]
    return f"{m.group(1)}/{repo}"


def looks_like_local_path(value: str) -> bool:
    v = value.strip()
    if not v:
        return False
    if v.startswith(("http://", "https://", "git@", "github.com")):
        return False
    if re.match(r"^[A-Za-z]:\\", v):
        return True
    if v.startswith(("/", "./", "../", "~")):
        return True
    return "\\" in v and "/" not in v.split("\\")[0]


def _is_git_repo(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def _search_roots() -> list[Path]:
    roots: list[Path] = []
    raw = settings.local_repo_search_roots.strip()
    if raw:
        for part in raw.replace(",", ";").split(";"):
            part = part.strip()
            if part:
                roots.append(Path(part))
    roots.extend(
        [
            settings.workspace_root.parent,
            Path.home() / "Projects",
            Path.home() / "source" / "repos",
            Path.home() / "dev",
        ]
    )
    seen: set[str] = set()
    unique: list[Path] = []
    for root in roots:
        key = str(root.resolve()) if root.exists() else str(root)
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return unique


def _candidate_folder_names(owner: str, repo: str) -> list[str]:
    return list(
        dict.fromkeys(
            [
                repo,
                f"{owner}-{repo}",
                f"{owner}_{repo}",
                repo.replace("_", "-"),
            ]
        )
    )


def _discover_git_repos_under(root: Path, *, max_depth: int = 2) -> list[Path]:
    """Find git checkouts under root (e.g. C:\\Software Projects\\*)."""
    found: list[Path] = []
    if not root.is_dir():
        return found

    def walk(path: Path, depth: int) -> None:
        if len(found) >= 80:
            return
        if _is_git_repo(path):
            found.append(path.resolve())
            return
        if depth <= 0:
            return
        skip = {
            "node_modules",
            ".venv",
            "venv",
            ".specwright",
            "__pycache__",
            ".git",
        }
        try:
            for child in path.iterdir():
                if child.is_dir() and child.name not in skip:
                    walk(child, depth - 1)
        except OSError:
            return

    walk(root, max_depth)
    return found


def find_local_checkout(owner: str, repo: str, *, explicit: Path | None = None) -> Path | None:
    """Return a local folder whose origin remote matches github.com/owner/repo."""
    cache = persistent_repo_path(owner, repo)
    checks: list[Path] = []
    if explicit is not None:
        checks.append(explicit.resolve())
    for root in _search_roots():
        if not root.is_dir():
            continue
        for name in _candidate_folder_names(owner, repo):
            checks.append((root / name).resolve())
        checks.extend(_discover_git_repos_under(root))

    seen: set[str] = set()
    cache_hit: Path | None = None

    def try_path(path: Path) -> Path | None:
        nonlocal cache_hit
        key = str(path)
        if key in seen:
            return None
        seen.add(key)
        if not _is_git_repo(path):
            return None
        origin = _git_origin_url(path)
        if not origin or not _remote_matches_github(origin, owner, repo):
            return None
        if path.resolve() == cache.resolve():
            cache_hit = path
            return None
        return path

    for path in checks:
        hit = try_path(path)
        if hit is not None:
            return hit

    if cache.exists():
        hit = try_path(cache.resolve())
        if hit is not None:
            return hit
    return cache_hit


def resolve_github_project_root(
    github_url: str,
    *,
    local_path: str | None = None,
    prefer_local: bool = True,
) -> tuple[Path, str, str, str, str]:
    """
    Resolve scan root for a GitHub URL.

    Returns (root_path, owner, repo, source, message) where source is 'local' or 'clone'.
    """
    owner, repo = parse_github_url(github_url)
    explicit = Path(local_path).resolve() if local_path and local_path.strip() else None

    if explicit is not None:
        if not explicit.is_dir():
            raise ValueError(f"Local path not found: {explicit}")
        if not _is_git_repo(explicit):
            raise ValueError(f"Not a git repository: {explicit}")
        origin = _git_origin_url(explicit)
        if not origin or not _remote_matches_github(origin, owner, repo):
            raise ValueError(
                f"Local path does not match {owner}/{repo} (origin: {origin or 'none'})"
            )
        return (
            explicit,
            owner,
            repo,
            "local",
            f"Scanning your local checkout at {explicit}",
        )

    if prefer_local:
        local = find_local_checkout(owner, repo)
        if local is not None:
            cache = persistent_repo_path(owner, repo)
            if local.resolve() == cache.resolve():
                msg = f"Using existing Specwright cache at {local}"
            else:
                msg = f"Found your local checkout — scanning {local} (not cloning from GitHub)"
            return local, owner, repo, "local", msg

    root, owner, repo = clone_or_update_github_repo(github_url)
    return (
        root,
        owner,
        repo,
        "clone",
        f"Cloned from GitHub into {root} — for your working copy, use Local path or set SPECWRIGHT_LOCAL_REPO_SEARCH_ROOTS",
    )
