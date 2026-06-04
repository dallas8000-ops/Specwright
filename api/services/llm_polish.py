"""Polish generated markdown via OpenAI-compatible chat API."""
from __future__ import annotations

from api.services.ai_client import chat_completion

POLISH_SYSTEM = """You are a technical writer. Improve the given API documentation markdown:
- Fix grammar and clarity
- Keep all paths, methods, and code identifiers exact
- Do not invent endpoints or models
- Return only the improved markdown, no preamble"""


async def polish_markdown(content: str, *, title: str = "API docs") -> str:
    return await chat_completion(
        system=POLISH_SYSTEM,
        user=f"Document title: {title}\n\n---\n\n{content[:12000]}",
        temperature=0.3,
    )
