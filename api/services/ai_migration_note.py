"""Generate PR migration guidance from OpenAPI diff and score delta."""
from __future__ import annotations

from api.services.ai_breaking_change import classify_pr_diff
from api.services.ai_client import chat_completion


async def generate_migration_note(
    *,
    pr_diff: dict | None,
    score: int | None,
    previous_score: int | None = None,
    project_name: str = "API",
) -> dict:
    triage = classify_pr_diff(pr_diff)
    if not pr_diff or not pr_diff.get("routes_changed"):
        return {
            "note": "No OpenAPI path changes in this scan — client integrations likely unchanged.",
            "triage": triage,
        }

    score_line = ""
    if score is not None:
        score_line = f"Current Specwright Score: {score}/100."
        if previous_score is not None and previous_score != score:
            delta = score - previous_score
            sign = "+" if delta > 0 else ""
            score_line += f" ({sign}{delta} vs previous scan)."

    breaking = [i for i in triage["items"] if i["classification"] == "breaking"]
    additive = [i for i in triage["items"] if i["classification"] == "additive"]

    system = """You write a short PR migration note for API consumers (3-5 sentences).
Rules:
- Mention only paths listed in the input
- State breaking vs additive changes clearly
- Suggest concrete client actions (update SDK, bump version, retest)
- No invented endpoints
- Plain markdown, no heading"""

    user = f"""Project: {project_name}
{score_line}
Breaking removals: {[i['path'] for i in breaking]}
Additive additions: {[i['path'] for i in additive]}
Diff summary: {pr_diff.get('summary', '')}
"""

    note = await chat_completion(system=system, user=user, temperature=0.3, max_tokens=512)
    return {"note": note.strip(), "triage": triage}
