"""
Deep Slack integration — actionable messages with Acknowledge / Escalate.
In production, POST to Slack incoming webhook or chat.postMessage with blocks.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def build_slack_blocks(alert) -> list[dict]:
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"⚠ {alert.title}"},
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": alert.message}},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Acknowledge"},
                    "style": "primary",
                    "action_id": f"ack_{alert.id}",
                    "value": str(alert.id),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Escalate"},
                    "style": "danger",
                    "action_id": f"esc_{alert.id}",
                    "value": str(alert.id),
                },
            ],
        },
    ]


def send_slack_actionable_alert(alert, action: str = "created"):
    webhook_url = getattr(settings, "SLACK_WEBHOOK_URL", None)
    payload = {
        "text": alert.title,
        "blocks": build_slack_blocks(alert),
        "metadata": {"alert_id": alert.id, "action": action},
    }
    if not webhook_url:
        logger.info("Slack webhook not configured. Payload: %s", payload)
        return False
    try:
        import httpx

        httpx.post(webhook_url, json=payload, timeout=10)
        return True
    except Exception:
        logger.exception("Slack delivery failed")
        return False


def handle_slack_interaction(payload: dict):
    """Process Slack interactive button callbacks."""
    from apps.intelligence.models import ProactiveAlert

    action = payload.get("actions", [{}])[0]
    action_id = action.get("action_id", "")
    alert_id = action.get("value")
    if not alert_id:
        return {"text": "Unknown action"}
    try:
        alert = ProactiveAlert.objects.get(id=alert_id)
    except ProactiveAlert.DoesNotExist:
        return {"text": "Alert not found"}
    if action_id.startswith("ack_"):
        alert.acknowledged = True
        alert.save(update_fields=["acknowledged"])
        return {"text": f"Acknowledged: {alert.title}"}
    if action_id.startswith("esc_"):
        alert.escalated = True
        alert.save(update_fields=["escalated"])
        return {"text": f"Escalated: {alert.title}"}
    return {"text": "OK"}
