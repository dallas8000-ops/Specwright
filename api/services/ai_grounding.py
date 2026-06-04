"""Ground AI responses in AST-discovered routes and handler source."""
from __future__ import annotations

import ast
import re
from pathlib import Path


def route_key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def known_route_index(routes: list[dict]) -> dict[str, dict]:
    return {route_key(r["method"], r["path"]): r for r in routes}


def known_paths(routes: list[dict]) -> set[str]:
    return {r["path"] for r in routes}


def validate_paths_in_text(text: str, allowed_paths: set[str]) -> list[str]:
    """Return API-like paths mentioned in text that are not in the allowed set."""
    mentioned = set(re.findall(r"`(/[^`]+)`", text))
    mentioned |= set(re.findall(r"(?<![\w/])(/[\w/{}\-._]+)", text))
    bad = []
    for p in mentioned:
        if p.startswith("/api/v1"):
            continue
        if p not in allowed_paths and "{" not in p:
            # Allow partial matches for templated paths
            if not any(
                ap == p or ap.replace("{", "").replace("}", "") in p for ap in allowed_paths
            ):
                bad.append(p)
    return bad


def handler_snippet(root: Path, route: dict, *, max_lines: int = 40) -> str:
    module = route.get("module", "")
    name = route.get("name", "")
    if not module or not name:
        return ""

    fp = root / module.replace("/", "\\") if "\\" in str(root) else root / module
    if not fp.exists():
        fp = root / module
    if not fp.exists():
        return ""

    try:
        text = fp.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except (SyntaxError, OSError):
        return ""

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            lines = text.splitlines()
            start = max(0, node.lineno - 1)
            end = min(len(lines), node.end_lineno or node.lineno)
            chunk = lines[start:end]
            if len(chunk) > max_lines:
                chunk = chunk[:max_lines] + ["    # ..."]
            return "\n".join(chunk)
    return ""


def build_chat_context(
    *,
    routes: list[dict],
    openapi: str,
    api_md: str,
    root: Path,
    max_routes: int = 24,
) -> str:
    parts = ["## Known routes (only reference these)\n"]
    for r in routes[:max_routes]:
        doc = (r.get("docstring") or r.get("summary") or "").strip().split("\n")[0]
        parts.append(f"- {r['method']} `{r['path']}` — `{r['name']}` — {doc}")
        snip = handler_snippet(root, r, max_lines=12)
        if snip:
            parts.append(f"```python\n{snip}\n```")
    if len(routes) > max_routes:
        parts.append(f"\n_({len(routes) - max_routes} more routes omitted)_\n")
    parts.append("\n## OpenAPI excerpt\n```yaml\n")
    parts.append(openapi[:6000])
    parts.append("\n```\n")
    if api_md:
        parts.append("\n## API markdown excerpt\n")
        parts.append(api_md[:4000])
    return "\n".join(parts)
