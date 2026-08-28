"""Optional CI and Notion sync after each scan."""
from __future__ import annotations

from pathlib import Path

from api.core.config import settings
from api.services.ci_template import generate_github_action
from api.services.notion_export import create_api_docs_page


CI_REL_PATH = ".github/workflows/specwright.yml"


def sync_ci_template(root: Path) -> str | None:
    """Write the Specwright GitHub Action workflow into the repo."""
    dest = root / CI_REL_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(generate_github_action(), encoding="utf-8", newline="\n")
    return CI_REL_PATH


async def run_post_scan_sync(project, artifacts: list, stats: dict) -> dict:
    """Sync CI yaml and optionally push API docs to Notion after a scan."""
    root = Path(project.root_path).resolve()
    out: dict = {"ci_synced": False, "notion_page_url": None}

    should_sync = project.watch_enabled or bool(stats.get("synced_files"))
    if settings.auto_ci_sync_on_scan and should_sync and root.exists():
        rel = sync_ci_template(root)
        if rel:
            out["ci_synced"] = True
            synced = list(stats.get("synced_files") or [])
            if rel not in synced:
                synced.append(rel)
            stats["synced_files"] = synced

    if (
        settings.auto_notion_on_scan
        and settings.notion_api_key
        and settings.notion_parent_page_id
    ):
        api_md = next((a for a in artifacts if a.kind == "api_docs"), None)
        if api_md and api_md.content.strip():
            try:
                page = await create_api_docs_page(
                    token=settings.notion_api_key,
                    parent_page_id=settings.notion_parent_page_id,
                    title=f"{project.name} API — Specwright",
                    markdown=api_md.content,
                )
                out["notion_page_url"] = page.get("url")
            except Exception as exc:
                out["notion_error"] = str(exc)[:200]

    return out
