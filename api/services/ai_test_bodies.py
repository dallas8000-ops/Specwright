"""Enhance pytest scaffolds with grounded AI-generated bodies."""
from __future__ import annotations

from api.analyzers.test_scaffold import generate_tests
from api.services.ai_client import chat_completion, extract_json_array
from api.services.ai_grounding import handler_snippet, known_paths
from pathlib import Path


async def enhance_test_scaffold(
    *,
    framework: str,
    routes: list[dict],
    models: list[dict],
    project_name: str,
    root: Path,
    max_tests: int = 12,
) -> dict:
    base = generate_tests(
        framework=framework,
        routes=routes,
        models=models,
        project_name=project_name,
    )
    if framework != "fastapi" or not routes:
        return {"content": base, "enhanced": 0}

    batch = routes[:max_tests]
    route_payload = []
    for r in batch:
        route_payload.append(
            {
                "method": r["method"],
                "path": r["path"],
                "name": r["name"],
                "docstring": (r.get("docstring") or "")[:300],
                "snippet": handler_snippet(root, r, max_lines=20),
            }
        )

    allowed = known_paths(routes)
    system = """You write pytest test function bodies for FastAPI TestClient.
Rules:
- Use exact paths and HTTP methods from input
- Return ONLY JSON array: [{"function_name":"test_...","body":"    response = client.get(...)\\n    assert ..."}]
- body is indented Python lines inside the function (no def line)
- Use status_code assertions (200, 201, 204, or < 500 for smoke)
- Do not invent routes
- Keep each test under 8 lines"""

    user = f"Enhance tests for:\n{route_payload}"
    raw = await chat_completion(system=system, user=user, temperature=0.2)
    enhancements = extract_json_array(raw)

    lines = base.splitlines()
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
                # Replace until next def or EOF
                j = i + 1
                while j < len(lines) and not lines[j].startswith("def "):
                    j += 1
                body_lines = [b if b.startswith("    ") else f"    {b}" for b in body.strip().splitlines()]
                lines = lines[: i + 1] + body_lines + lines[j:]
                enhanced += 1
                break

    return {"content": "\n".join(lines) + "\n", "enhanced": enhanced}
