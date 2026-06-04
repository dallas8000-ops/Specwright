"""Write generated artifacts to the codebase (live sync)."""
from __future__ import annotations

from pathlib import Path


def sync_artifacts_to_disk(root: Path, artifacts: list) -> list[str]:
    """Persist scan artifacts under project root. Returns written paths."""
    written: list[str] = []
    for art in artifacts:
        rel = (art.file_path or "").strip().lstrip("/\\")
        if not rel or ".." in rel.replace("\\", "/"):
            continue
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(art.content, encoding="utf-8", newline="\n")
        written.append(rel)
    return written
