import json
import logging
import re

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def call_llm(*, system: str, user: str) -> dict | None:
    api_key = getattr(settings, "AI_API_KEY", None) or ""
    base_url = getattr(settings, "AI_API_BASE_URL", "https://api.openai.com/v1")
    model = getattr(settings, "AI_MODEL", "gpt-4o-mini")

    if not api_key:
        return None

    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return _parse_json(content)
    except Exception:
        logger.exception("LLM call failed")
        return None


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        raise


def heuristic_triage(vertical: str, case_payload: dict) -> dict:
    """Deterministic fallback when no API key — still vertical-specific, not generic."""
    priority = case_payload.get("priority", "normal")
    stage = case_payload.get("stage", "intake")
    title = case_payload.get("title", "Case")

    risks = []
    if priority in ("critical", "high"):
        risks.append(
            {
                "severity": "critical",
                "title": "Elevated priority",
                "detail": "Executive visibility likely required within 24h.",
            }
        )

    if vertical == "legal":
        risks.append(
            {
                "severity": "warning",
                "title": "Pre-signature exposure",
                "detail": "Counsel review gates revenue recognition and liability until cleared.",
            }
        )
        action = "Route to lead counsel; extract key terms (liability cap, indemnity, term) before approval."
    elif vertical == "hr":
        risks.append(
            {
                "severity": "warning",
                "title": "Start-date dependency",
                "detail": "Delayed onboarding blocks payroll, access, and manager capacity planning.",
            }
        )
        action = "Confirm start date with hiring manager; open IT provisioning parallel to HR checklist."
    else:
        risks.append(
            {
                "severity": "warning",
                "title": "SLA / OTIF exposure",
                "detail": "Carrier delay may trigger customer penalties without proactive comms.",
            }
        )
        action = "Query carrier ETA; if >24h slip, escalate to ops lead and draft customer delay notice."

    if stage == "intake":
        action = f"Complete intake validation, then: {action}"

    return {
        "summary": f"AI triage for «{title}» — {vertical} vertical, stage {stage}.",
        "risks": risks,
        "recommended_action": action,
        "confidence": 0.72,
        "reasoning": "Heuristic vertical engine (configure AI_API_KEY for full LLM reasoning).",
        "suggested_stage_advance": stage == "intake",
        "draft_communication": "",
        "provider": "heuristic",
    }
