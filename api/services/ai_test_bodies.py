"""Enhance pytest scaffolds with grounded AI-generated bodies."""
from __future__ import annotations

from api.analyzers.test_scaffold import generate_tests
from api.services.ai_client import chat_completion, extract_json_array
from api.services.ai_grounding import handler_snippet, known_paths
from pathlib import Path


def _test_function_name(route: dict) -> str:
    return (
        f"test_{route['name']}_{route['method'].lower()}".replace("-", "_").replace("/", "_")[:60]
    )


def _apply_enhancements(lines: list[str], enhancements: list[dict], allowed: set[str]) -> int:
    enhanced = 0
    for item in enhancements:
        fname = item.get("function_name", "")
        body = item.get("body", "")
        if not fname.startswith("test_") or not body:
            continue
        if allowed and not any(p in body for p in allowed):
            continue
        for i, line in enumerate(lines):
            if line.startswith(f"def {fname}("):
                j = i + 1
                while j < len(lines) and not lines[j].startswith("def "):
                    j += 1
                body_lines = [
                    b if b.startswith("    ") else f"    {b}" for b in body.strip().splitlines()
                ]
                lines[:] = lines[: i + 1] + body_lines + lines[j:]
                enhanced += 1
                break
    return enhanced


async def _enhance_batch(
    *,
    lines: list[str],
    batch: list[dict],
    routes: list[dict],
    root: Path,
) -> int:
    if not batch:
        return 0
    route_payload = []
    for r in batch:
        route_payload.append(
            {
                "method": r["method"],
                "path": r["path"],
                "name": r["name"],
                "function_name": _test_function_name(r),
                "docstring": (r.get("docstring") or "")[:300],
                "snippet": handler_snippet(root, r, max_lines=20),
            }
        )
    allowed = known_paths(routes)
    system = """You write pytest test function bodies for FastAPI TestClient.
Rules:
- Use exact paths and HTTP methods from input
- Return ONLY JSON array: [{"function_name":"test_...","body":"    response = client.get(...)\\n    assert ..."}]
- function_name must match the input function_name when provided
- body is indented Python lines inside the function (no def line)
- Use status_code assertions (200, 201, 204, or < 500 for smoke)
- Do not invent routes
- Keep each test under 8 lines"""

    user = f"Enhance tests for:\n{route_payload}"
    raw = await chat_completion(system=system, user=user, temperature=0.2)
    enhancements = extract_json_array(raw)
    return _apply_enhancements(lines, enhancements, allowed)


async def enhance_test_scaffold(
    *,
    framework: str,
    routes: list[dict],
    models: list[dict],
    project_name: str,
    root: Path,
    max_tests: int = 15,
    max_batches: int = 6,
    base_content: str | None = None,
) -> dict:
    base = base_content or generate_tests(
        framework=framework,
        routes=routes,
        models=models,
        project_name=project_name,
    )
    if framework != "fastapi" or not routes:
        return {"content": base, "enhanced": 0}

    lines = base.splitlines()
    enhanced = 0
    # Process routes in batches (prioritize the list passed in — usually uncovered routes).
    for batch_start in range(0, min(len(routes), max_tests * max_batches), max_tests):
        batch = routes[batch_start : batch_start + max_tests]
        enhanced += await _enhance_batch(
            lines=lines, batch=batch, routes=routes, root=root
        )

    return {"content": "\n".join(lines) + "\n", "enhanced": enhanced}
