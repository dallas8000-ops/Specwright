from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def send_workflow_notification(run, node, context: dict):
    config = node.config
    title = config.get("title", f"Workflow update: {run.workflow.name}")
    body = config.get("body", "A workflow step requires your attention.")
    recipient_id = config.get("recipient_id") or run.triggered_by_id
    if not recipient_id:
        return
    Notification.objects.create(
        recipient_id=recipient_id,
        title=title,
        body=body,
        channel=Notification.Channel.IN_APP,
        priority=config.get("priority", Notification.Priority.NORMAL),
        link=f"/runs/{run.id}",
        metadata={"run_id": str(run.id), "node_key": node.key},
    )
