"""Classify OpenAPI path diffs as breaking, additive, or documentation-only."""
from __future__ import annotations


def classify_pr_diff(pr_diff: dict | None) -> dict:
    if not pr_diff:
        return {
            "summary": "No API path changes detected.",
            "items": [],
            "breaking_count": 0,
            "additive_count": 0,
        }

    items = []
    for path in pr_diff.get("removed_paths", []):
        items.append(
            {
                "path": path,
                "change": "removed",
                "classification": "breaking",
                "reason": "Clients calling this path will receive 404.",
            }
        )
    for path in pr_diff.get("added_paths", []):
        items.append(
            {
                "path": path,
                "change": "added",
                "classification": "additive",
                "reason": "New capability; existing clients are unaffected.",
            }
        )

    breaking = sum(1 for i in items if i["classification"] == "breaking")
    additive = sum(1 for i in items if i["classification"] == "additive")
    summary_parts = []
    if breaking:
        summary_parts.append(f"{breaking} breaking")
    if additive:
        summary_parts.append(f"{additive} additive")
    summary = ", ".join(summary_parts) if summary_parts else "No path-level changes"

    return {
        "summary": summary,
        "items": items,
        "breaking_count": breaking,
        "additive_count": additive,
    }
