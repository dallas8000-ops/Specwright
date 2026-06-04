"""Scoped how-to chat grounded in project OpenAPI and handlers."""
from __future__ import annotations

from pathlib import Path

from api.services.ai_client import chat_completion
from api.services.ai_grounding import build_chat_context, validate_paths_in_text, known_paths


CHAT_SYSTEM = """You are Specwright, an API assistant for ONE codebase.
Rules:
- Answer only using the routes and snippets provided
- If the answer is not in context, say you don't see that endpoint
- Cite paths in backticks like `GET /users`
- Never invent endpoints or fields
- Be concise (under 200 words)"""


async def ask_api_question(
    *,
    question: str,
    routes: list[dict],
    openapi: str,
    api_md: str,
    root: Path,
) -> dict:
    context = build_chat_context(
        routes=routes,
        openapi=openapi,
        api_md=api_md,
        root=root,
    )
    user = f"{context}\n\n## Question\n{question.strip()}"
    answer = await chat_completion(system=CHAT_SYSTEM, user=user, temperature=0.2, max_tokens=800)

    allowed = known_paths(routes)
    unknown = validate_paths_in_text(answer, allowed)
    if unknown:
        answer += (
            "\n\n_Note: response mentioned paths not in the scan — verify before use: "
            + ", ".join(unknown[:5])
            + "_"
        )

    sources = [
        {"method": r["method"], "path": r["path"], "handler": r["name"]}
        for r in routes[:12]
        if r["path"].lower() in question.lower() or r["name"].lower() in question.lower()
    ][:6]

    return {"answer": answer, "sources": sources}
