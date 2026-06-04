"""Push generated markdown to Notion."""
from __future__ import annotations

import httpx


async def create_api_docs_page(
    *,
    token: str,
    parent_page_id: str,
    title: str,
    markdown: str,
) -> dict:
    """Create a Notion page with API reference content (paragraph blocks)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    chunks = _chunk_text(markdown, 1900)
    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": chunk}}],
            },
        }
        for chunk in chunks[:80]
    ]

    payload = {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {"title": [{"text": {"content": title[:2000]}}]},
        },
        "children": children[:100],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    return {"id": data.get("id"), "url": data.get("url")}


def _chunk_text(text: str, size: int) -> list[str]:
    lines = text.split("\n")
    chunks: list[str] = []
    buf: list[str] = []
    length = 0
    for line in lines:
        if length + len(line) > size and buf:
            chunks.append("\n".join(buf))
            buf = []
            length = 0
        buf.append(line)
        length += len(line) + 1
    if buf:
        chunks.append("\n".join(buf))
    return chunks or [text[:size]]
