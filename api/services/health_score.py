"""Specwright Score, route coverage map, and drift detection."""
from __future__ import annotations

import json
import re
from pathlib import Path

from api.analyzers.discovery import collect_python_files, detect_framework
from api.analyzers.route_collector import collect_all_routes
from api.analyzers.route_collector import collect_all_routes


def _route_key(route: dict) -> str:
    return f"{route.get('method', 'GET')} {route.get('path', '/')}"


def _tests_for_routes(test_content: str, routes: list[dict]) -> dict[str, bool]:
    covered: dict[str, bool] = {}
    for r in routes:
        key = _route_key(r)
        path = r.get("path", "")
        name = r.get("name", "")
        # Match quoted paths in generated tests (avoids /health matching /health/scheduler).
        quoted = (
            f"'{path}'",
            f'"{path}"',
            f"'{path.replace('{', '').replace('}', '')}'",
        )
        fname = f"test_{name}_{r.get('method', 'get').lower()}"
        covered[key] = any(q in test_content for q in quoted if q not in ("''", '""')) or (
            name and fname in test_content
        )
    return covered


def _docs_for_routes(openapi: str, api_md: str, routes: list[dict]) -> dict[str, bool]:
    covered: dict[str, bool] = {}
    for r in routes:
        key = _route_key(r)
        path = r.get("path", "")
        name = r.get("name", "")
        in_spec = path in openapi or (name and name in openapi)
        in_md = path in api_md or (name and name in api_md)
        covered[key] = in_spec and in_md
    return covered


def route_status(test: bool, doc: bool) -> str:
    if test and doc:
        return "green"
    if test or doc:
        return "amber"
    return "red"


def compute_coverage_map(
    routes: list[dict], test_content: str, openapi: str, api_md: str
) -> list[dict]:
    tests = _tests_for_routes(test_content, routes)
    docs = _docs_for_routes(openapi, api_md, routes)
    rows = []
    for r in routes:
        key = _route_key(r)
        t = tests.get(key, False)
        d = docs.get(key, False)
        rows.append(
            {
                "method": r.get("method", "GET"),
                "path": r.get("path", "/"),
                "handler": r.get("name", ""),
                "summary": r.get("summary", ""),
                "has_test": t,
                "has_docs": d,
                "status": route_status(t, d),
            }
        )
    return rows


def uncovered_routes(routes: list[dict], test_content: str) -> list[dict]:
    """Routes with no pytest scaffold detected in test_content."""
    rows = compute_coverage_map(routes, test_content, "", "")
    missing = {(r["method"], r["path"]) for r in rows if not r["has_test"]}
    return [r for r in routes if (r.get("method"), r.get("path")) in missing]


def enrich_coverage_labels(
    rows: list[dict], *, added_paths: list[str] | None = None
) -> list[dict]:
    added = set(added_paths or [])
    for row in rows:
        row["status_label"] = _route_status_label(row, added)
    return rows


def _route_status_label(row: dict, added_paths: set[str]) -> str:
    if row["path"] in added_paths:
        return "New in PR"
    if row["has_test"] and row["has_docs"]:
        return "Fully covered"
    if not row["has_test"] and not row["has_docs"]:
        return "No test, no docs"
    if not row["has_test"]:
        return "No test"
    if not row["has_docs"]:
        return "No docs"
    return "Partial"


def _model_doc_pct(models_md: str, models_count: int) -> float:
    if models_count == 0:
        return 100.0
    if not models_md or "No models" in models_md:
        return 0.0
    documented = len(re.findall(r"^###\s+\w+", models_md, re.M))
    if documented == 0:
        documented = models_md.count("| Field |")
    return min(100.0, round((documented / max(models_count, 1)) * 100, 1))


def compute_score(
    routes: list[dict],
    coverage_rows: list[dict],
    drift_commits: int,
    models_count: int,
    *,
    models_md: str = "",
) -> dict:
    n = len(routes) or 1
    green = sum(1 for r in coverage_rows if r["status"] == "green")
    amber = sum(1 for r in coverage_rows if r["status"] == "amber")
    test_pct = sum(1 for r in coverage_rows if r["has_test"]) / n * 100
    doc_pct = sum(1 for r in coverage_rows if r["has_docs"]) / n * 100
    full_pct = green / n * 100

    # Weights: docs 35%, tests 35%, full route health 20%, freshness 10%
    freshness = max(0, 100 - min(drift_commits * 8, 100))
    model_pct = _model_doc_pct(models_md, models_count)
    raw = (
        doc_pct * 0.30
        + test_pct * 0.30
        + full_pct * 0.15
        + freshness * 0.10
        + model_pct * 0.15
    )
    score = int(min(100, max(0, round(raw))))

    gaps = {
        "no_test": sum(1 for r in coverage_rows if not r["has_test"]),
        "no_docs": sum(1 for r in coverage_rows if not r["has_docs"]),
        "red_routes": sum(1 for r in coverage_rows if r["status"] == "red"),
        "amber_routes": amber,
    }

    return {
        "score": score,
        "grade": _grade(score),
        "breakdown": {
            "documentation_pct": round(doc_pct, 1),
            "test_coverage_pct": round(test_pct, 1),
            "fully_covered_pct": round(full_pct, 1),
            "freshness_pct": round(freshness, 1),
            "model_documentation_pct": model_pct,
        },
        "gaps": gaps,
        "summary": _score_summary(score, gaps, len(routes)),
    }


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _score_summary(score: int, gaps: dict, routes: int) -> str:
    if score >= 85:
        return f"Strong API health across {routes} routes."
    parts = []
    if gaps["no_docs"]:
        parts.append(f"{gaps['no_docs']} route(s) lack documentation")
    if gaps["no_test"]:
        parts.append(f"{gaps['no_test']} route(s) lack tests")
    if not parts:
        return f"Score {score}/100 — {routes} routes tracked."
    return f"Score {score}/100 — " + "; ".join(parts) + "."


def detect_drift(root: Path, generated_openapi: str) -> dict:
    """Compare on-disk OpenAPI vs latest generation."""
    spec_path = root / "docs" / "openapi.yaml"
    code_mtime = _codebase_mtime(root)
    spec_mtime = spec_path.stat().st_mtime if spec_path.exists() else 0

    on_disk = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
    drift = on_disk.strip() != generated_openapi.strip() if on_disk else True

    # Staleness proxy: how far spec file lagged behind code changes
    lag_seconds = max(0, code_mtime - spec_mtime) if spec_path.exists() else code_mtime
    commits_behind = min(99, int(lag_seconds / 3600) + (1 if drift else 0))

    return {
        "drift_detected": drift,
        "commits_behind": commits_behind,
        "message": (
            f"Your OpenAPI spec is ~{commits_behind} commit(s) behind your codebase."
            if drift or commits_behind > 0
            else "OpenAPI spec is in sync with your codebase."
        ),
        "spec_path": str(spec_path) if spec_path.exists() else None,
        "code_last_changed": code_mtime,
        "spec_last_written": spec_mtime,
    }


def _codebase_mtime(root: Path) -> float:
    latest = 0.0
    skip = {".venv", "venv", "node_modules", "__pycache__", ".git"}
    for path in root.rglob("*.py"):
        if any(s in path.parts for s in skip):
            continue
        try:
            latest = max(latest, path.stat().st_mtime)
        except OSError:
            pass
    return latest


def diff_openapi(old_yaml: str, new_yaml: str) -> dict:
    old_paths = set(re.findall(r"^  (/[^:]+):", old_yaml, re.M))
    new_paths = set(re.findall(r"^  (/[^:]+):", new_yaml, re.M))
    added = sorted(new_paths - old_paths)
    removed = sorted(old_paths - new_paths)
    changed_count = len(added) + len(removed)
    return {
        "added_paths": added,
        "removed_paths": removed,
        "routes_changed": changed_count,
        "summary": _pr_summary(added, removed),
    }


def _pr_summary(added: list[str], removed: list[str]) -> str:
    parts = []
    if added:
        parts.append(f"{len(added)} new endpoint(s)")
    if removed:
        parts.append(f"{len(removed)} removed endpoint(s)")
    undocumented = len(added)
    if not parts:
        return "No OpenAPI path changes detected."
    line = ", ".join(parts)
    if undocumented:
        line += f" — {undocumented} may need documentation review"
    return line


def build_metrics(
    coverage: list[dict], models_count: int, models_md: str, drift: dict, pr_diff: dict | None
) -> dict:
    n = len(coverage) or 1
    docs_n = sum(1 for r in coverage if r["has_docs"])
    tests_n = sum(1 for r in coverage if r["has_test"])
    models_doc = int(_model_doc_pct(models_md, models_count) / 100 * models_count) if models_count else 0
    added = len((pr_diff or {}).get("added_paths", []))
    return {
        "routes_documented": {"current": docs_n, "total": len(coverage)},
        "routes_documented_delta": added,
        "tests_generated": {
            "current": tests_n,
            "total": len(coverage),
            "uncovered": len(coverage) - tests_n,
        },
        "models_documented": {
            "current": models_doc,
            "total": models_count,
            "missing": max(0, models_count - models_doc),
        },
        "spec_drift": drift["commits_behind"],
        "spec_in_sync": not drift["drift_detected"],
    }


def build_alerts(
    coverage: list[dict],
    pr_diff: dict | None,
    *,
    ai: dict | None = None,
    route_count: int | None = None,
    framework: str | None = None,
) -> dict:
    total_routes = route_count if route_count is not None else len(coverage)
    zero_routes_banner = None
    if total_routes == 0:
        hint = (
            "Django API routes live in urls.py — rescan after updating Specwright, "
            "or point the project at apps/backend."
            if framework == "django"
            else "No HTTP routes found — check repo path or framework."
        )
        zero_routes_banner = {
            "message": f"0 API routes detected. {hint}",
        }

    no_test = [r for r in coverage if not r["has_test"]]
    test_samples = [
        f"{r['method']} {r['path']}" for r in no_test[:3]
    ]
    test_banner = None
    if no_test:
        extra = len(no_test) - len(test_samples)
        suffix = f", and {extra} others" if extra > 0 else ""
        test_banner = {
            "count": len(no_test),
            "samples": test_samples,
            "message": (
                f"{len(no_test)} routes have no test scaffold — "
                f"{', '.join(test_samples)}{suffix}."
            ),
        }

    pr_banner = None
    if pr_diff and pr_diff.get("routes_changed", 0) > 0:
        added = pr_diff.get("added_paths", [])
        pr_banner = {
            "routes_changed": pr_diff["routes_changed"],
            "added_count": len(added),
            "summary": pr_diff.get("summary", ""),
            "message": (
                f"PR scan detected {len(added)} new route(s) — spec updated automatically."
                if added
                else pr_diff.get("summary", "API spec changed.")
            ),
            "migration_note": (ai or {}).get("migration_note"),
        }

    description_banner = None
    gap_count = (ai or {}).get("description_gaps", 0)
    filled = (ai or {}).get("descriptions_filled", 0)
    if gap_count > 0 and filled == 0:
        description_banner = {
            "count": gap_count,
            "message": (
                f"{gap_count} route(s) have weak or missing OpenAPI descriptions — "
                "fill from handler docstrings."
            ),
        }
    elif filled > 0:
        description_banner = {
            "count": 0,
            "filled": filled,
            "message": f"AI filled {filled} OpenAPI description(s) on this scan.",
        }

    return {
        "test_gap": test_banner,
        "pr_update": pr_banner,
        "description_gap": description_banner,
        "zero_routes": zero_routes_banner,
    }


def build_project_health(
    root: Path, artifacts: list, previous_openapi: str | None = None
) -> dict:
    files = collect_python_files(root)
    framework = detect_framework(root)
    routes = collect_all_routes(files, root, framework)

    by_kind = {a.kind: a.content for a in artifacts}
    openapi = by_kind.get("openapi", "")
    api_md = by_kind.get("api_docs", "")
    tests = by_kind.get("tests", "")
    models_md = by_kind.get("django_docs", "")

    coverage = compute_coverage_map(routes, tests, openapi, api_md)
    drift = detect_drift(root, openapi)

    pr_diff = None
    if previous_openapi:
        pr_diff = diff_openapi(previous_openapi, openapi)

    coverage = enrich_coverage_labels(
        coverage, added_paths=(pr_diff or {}).get("added_paths")
    )
    models_count = _count_models(files, root)
    score_data = compute_score(
        routes,
        coverage,
        drift["commits_behind"],
        models_count,
        models_md=models_md,
    )
    metrics = build_metrics(coverage, models_count, models_md, drift, pr_diff)
    alerts = build_alerts(
        coverage,
        pr_diff,
        route_count=len(routes),
        framework=framework,
    )

    return {
        "score": score_data,
        "coverage": coverage,
        "drift": drift,
        "pr_diff": pr_diff,
        "route_count": len(routes),
        "models_count": models_count,
        "metrics": metrics,
        "alerts": alerts,
    }


def _count_models(files: list[Path], root: Path) -> int:
    import ast

    n = 0
    for fp in files:
        if "model" not in fp.name.lower():
            continue
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                n += 1
    return n


def health_from_scan_stats(stats_json: str, coverage: list, drift: dict, score: dict) -> str:
    return json.dumps({"stats": json.loads(stats_json), "coverage": coverage, "drift": drift, "score": score})
