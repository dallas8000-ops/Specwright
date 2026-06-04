"""Proactive drift alerts via Slack webhook."""
from __future__ import annotations

import httpx

from api.core.config import settings


async def send_slack_alert(webhook_url: str, text: str, *, blocks: list | None = None) -> bool:
    if not webhook_url:
        return False
    payload: dict = {"text": text}
    if blocks:
        payload["blocks"] = blocks
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(webhook_url, json=payload)
        return resp.is_success


async def notify_drift(
    project_name: str,
    drift_message: str,
    score: int,
    webhook_url: str | None = None,
) -> bool:
    url = webhook_url or settings.slack_webhook_url
    if not url:
        return False
    text = (
        f":warning: *Specwright drift* — `{project_name}`\n"
        f"{drift_message}\n"
        f"Health score: *{score}/100* — open Specwright to sync."
    )
    return await send_slack_alert(url, text)
