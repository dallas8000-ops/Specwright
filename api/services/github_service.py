"""GitHub PR comments and webhook handling."""
from __future__ import annotations

import hashlib
import hmac
import json

import httpx

from api.core.config import settings


def verify_webhook_signature(body: bytes, signature: str | None) -> bool:
    secret = settings.github_webhook_secret
    if not secret:
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature[7:], expected)


async def post_pr_comment(repo: str, pr_number: int, body: str) -> dict:
    token = settings.github_token
    if not token:
        raise ValueError(
            "GitHub is not configured. Set SPECWRIGHT_GITHUB_TOKEN (repo scope: pull requests)."
        )
    if "/" not in repo:
        raise ValueError("github_repo must be owner/repo")

    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json={"body": body})
        resp.raise_for_status()
        return resp.json()


def format_pr_comment(
    project_name: str,
    scan_summary: str,
    artifact_lines: list[str],
    *,
    pr_diff: dict | None = None,
    score: int | None = None,
    coverage_gaps: dict | None = None,
    breaking_triage: dict | None = None,
    migration_note: str | None = None,
    reconcile_count: int = 0,
) -> str:
    lines = [
        "## Specwright — PR documentation check",
        "",
        f"**Project:** {project_name}",
    ]
    if score is not None:
        lines.append(f"**Specwright Score:** {score}/100")
    lines.append("")

    if pr_diff and pr_diff.get("routes_changed", 0) > 0:
        lines.append(f"### API changes — {pr_diff.get('summary', '')}")
        for p in pr_diff.get("added_paths", [])[:8]:
            lines.append(f"- ➕ `{p}`")
        for p in pr_diff.get("removed_paths", [])[:8]:
            lines.append(f"- ➖ `{p}`")
        lines.append("")

    if breaking_triage and breaking_triage.get("items"):
        lines.append("### Breaking-change triage")
        lines.append(f"_{breaking_triage.get('summary', '')}_")
        for item in breaking_triage["items"][:10]:
            icon = "🔴" if item["classification"] == "breaking" else "🟢"
            lines.append(
                f"- {icon} **{item['classification']}** `{item['path']}` — {item['reason']}"
            )
        lines.append("")

    if migration_note:
        lines.append("### Client migration note")
        lines.append(migration_note.strip())
        lines.append("")

    if reconcile_count > 0:
        lines.append(
            f"### Docstring ↔ spec\n{reconcile_count} handler docstring(s) "
            "differ from generated OpenAPI summaries — run **AI reconcile** in Specwright."
        )
        lines.append("")

    if coverage_gaps:
        red = coverage_gaps.get("red_routes", 0)
        no_test = coverage_gaps.get("no_test", 0)
        if red or no_test:
            lines.append("### Coverage gaps")
            if red:
                lines.append(f"- {red} route(s) missing both tests and docs")
            if no_test:
                lines.append(f"- {no_test} route(s) have no test scaffold coverage")
            lines.append("")

    lines.append(scan_summary)
    lines.append("")
    lines.append("### Synced artifacts")
    for line in artifact_lines[:10]:
        lines.append(f"- {line}")
    lines.extend(
        [
            "",
            "_Specwright — the documentation layer for your API. OpenAPI + tests updated from code._",
        ]
    )
    return "\n".join(lines)


def parse_webhook_repo(payload: dict) -> tuple[str | None, int | None, str]:
    """Return (owner/repo, pr_number, action)."""
    action = payload.get("action", "")
    pr = payload.get("pull_request") or {}
    number = pr.get("number")
    repo = payload.get("repository") or {}
    full_name = repo.get("full_name")
    return full_name, number, action
