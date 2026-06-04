"""Shared OpenAI-compatible chat client for Specwright AI features."""
from __future__ import annotations

import json
import re

import httpx

from api.core.config import settings


def ai_configured() -> bool:
    return bool(settings.ai_api_key)


async def chat_completion(
    *,
    system: str,
    user: str,
    temperature: float = 0.25,
    max_tokens: int = 4096,
) -> str:
    if not settings.ai_api_key:
        raise ValueError(
            "AI is not configured. Set SPECWRIGHT_AI_API_KEY in your environment."
        )

    url = f"{settings.ai_api_base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user[:48000]},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {settings.ai_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    choice = data.get("choices", [{}])[0]
    text = (choice.get("message") or {}).get("content", "").strip()
    if not text:
        raise ValueError("AI returned empty content")
    return text


def extract_json_array(text: str) -> list:
    """Parse JSON array from model output (may be wrapped in markdown)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    if text.startswith("["):
        return json.loads(text)
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("AI response did not contain a JSON array")


def extract_json_object(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    if text.startswith("{"):
        return json.loads(text)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("AI response did not contain a JSON object")
