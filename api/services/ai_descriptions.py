"""Fill missing or weak OpenAPI summaries/descriptions using grounded LLM."""
from __future__ import annotations

import re

from api.services.ai_client import chat_completion, extract_json_array
from api.services.ai_grounding import known_paths, validate_paths_in_text

WEAK_SUMMARIES = {"", "Discovered route", "handler"}


def _needs_description(route: dict, spec_summary: str) -> bool:
    if spec_summary in WEAK_SUMMARIES:
        return True
    auto = route["name"].replace("_", " ").title()
    return spec_summary == auto or len(spec_summary) < 8


def find_description_gaps(routes: list[dict], openapi: str) -> list[dict]:
    from api.services.ai_docstring_reconcile import _openapi_summaries

    spec = _openapi_summaries(openapi)
    gaps = []
    for r in routes:
        key = (r["path"], r["method"])
        summary = spec.get(key, r.get("summary", ""))
        if _needs_description(r, summary):
            gaps.append(
                {
                    "method": r["method"],
                    "path": r["path"],
                    "handler": r["name"],
                    "current_summary": summary,
                    "docstring": (r.get("docstring") or "").split("\n")[0],
                }
            )
    return gaps


def _apply_description_updates(openapi: str, updates: list[dict]) -> tuple[str, int]:
    lines = openapi.splitlines()
    current_path = None
    current_method = None
    applied = 0

    update_map = {
        (u["path"], u["method"].upper()): u for u in updates
    }

    i = 0
    while i < len(lines):
        line = lines[i]
        path_m = re.match(r"^  (/[^:]+):\s*$", line)
        if path_m:
            current_path = path_m.group(1)
            current_method = None
            i += 1
            continue
        method_m = re.match(r"^    (get|post|put|patch|delete):\s*$", line, re.I)
        if method_m and current_path:
            current_method = method_m.group(1).upper()
            i += 1
            continue

        if current_path and current_method and (current_path, current_method) in update_map:
            u = update_map[(current_path, current_method)]
            if line.strip().startswith("summary:"):
                lines[i] = f"      summary: {u['summary']!r}"
                applied += 1
                # Insert description after summary if provided
                if u.get("description") and (
                    i + 1 >= len(lines) or not lines[i + 1].strip().startswith("description:")
                ):
                    lines.insert(i + 1, f"      description: {u['description']!r}")
                i += 1
                continue
        i += 1

    return "\n".join(lines) + ("\n" if openapi.endswith("\n") else ""), applied


async def fill_openapi_descriptions(
    routes: list[dict], openapi: str, *, max_routes: int = 20
) -> dict:
    gaps = find_description_gaps(routes, openapi)[:max_routes]
    if not gaps:
        return {"openapi": openapi, "filled": 0, "gaps": []}

    allowed = known_paths(routes)
    system = """You improve OpenAPI operation summaries and descriptions.
Rules:
- Only use paths and methods from the input JSON
- Never invent endpoints
- Prefer docstring text when present
- Return ONLY a JSON array: [{"method":"GET","path":"/x","summary":"...","description":"..."}]
- description is one short paragraph max"""

    user = f"Fill documentation gaps:\n{gaps}"
    raw = await chat_completion(system=system, user=user, temperature=0.2)
    updates = extract_json_array(raw)

    validated = []
    for u in updates:
        path = u.get("path", "")
        method = u.get("method", "GET").upper()
        if path not in allowed:
            continue
        if not any(r["path"] == path and r["method"] == method for r in routes):
            continue
        summary = (u.get("summary") or "").strip()
        if not summary:
            continue
        validated.append(
            {
                "method": method,
                "path": path,
                "summary": summary[:200],
                "description": (u.get("description") or "")[:500],
            }
        )

    merged, count = _apply_description_updates(openapi, validated)
    bad = validate_paths_in_text(merged, allowed)
    if bad:
        raise ValueError(f"AI referenced unknown paths: {', '.join(bad[:5])}")

    return {"openapi": merged, "filled": count, "gaps": gaps, "updates": validated}
