"""Compare handler docstrings with generated OpenAPI summaries."""
from __future__ import annotations

import re


def _openapi_summaries(openapi: str) -> dict[tuple[str, str], str]:
    """Map (path, METHOD) -> summary from generated OpenAPI yaml."""
    out: dict[tuple[str, str], str] = {}
    current_path = None
    current_method = None
    for line in openapi.splitlines():
        path_m = re.match(r"^  (/[^:]+):\s*$", line)
        if path_m:
            current_path = path_m.group(1)
            current_method = None
            continue
        method_m = re.match(r"^    (get|post|put|patch|delete):\s*$", line, re.I)
        if method_m and current_path:
            current_method = method_m.group(1).upper()
            continue
        sum_m = re.match(r"^      summary:\s*(.+)\s*$", line)
        if sum_m and current_path and current_method:
            raw = sum_m.group(1).strip().strip("'\"")
            out[(current_path, current_method)] = raw
    return out


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def reconcile_docstrings(routes: list[dict], openapi: str) -> list[dict]:
    spec = _openapi_summaries(openapi)
    mismatches = []
    for r in routes:
        doc = (r.get("docstring") or "").strip()
        if not doc:
            continue
        doc_first = doc.split("\n")[0].strip()
        key = (r["path"], r["method"])
        spec_sum = spec.get(key, r.get("summary", ""))
        if not spec_sum:
            continue
        if _normalize(doc_first) == _normalize(spec_sum):
            continue
        if spec_sum in ("Discovered route",) or spec_sum == r["name"].replace("_", " ").title():
            mismatches.append(
                {
                    "method": r["method"],
                    "path": r["path"],
                    "handler": r["name"],
                    "docstring": doc_first,
                    "openapi_summary": spec_sum,
                    "suggestion": f"Set OpenAPI summary to: {doc_first!r}",
                }
            )
        elif _normalize(doc_first) not in _normalize(spec_sum) and _normalize(spec_sum) not in _normalize(
            doc_first
        ):
            mismatches.append(
                {
                    "method": r["method"],
                    "path": r["path"],
                    "handler": r["name"],
                    "docstring": doc_first,
                    "openapi_summary": spec_sum,
                    "suggestion": f"Align spec with docstring: {doc_first!r}",
                }
            )
    return mismatches
