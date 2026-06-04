from datetime import timedelta

from django.utils import timezone

from apps.events.bus import publish_domain_event
from apps.events.types import EventType, Service

from .models import ApprovalRequest


def create_approval_request(run, node, context: dict):
    config = node.config
    due_hours = config.get("sla_hours", 48)
    approval = ApprovalRequest.objects.create(
        run=run,
        node_key=node.key,
        title=config.get("title", f"Approval: {node.label}"),
        description=config.get("description", ""),
        approver_group=config.get("approver_group", ""),
        due_at=timezone.now() + timedelta(hours=due_hours),
        payload={"context_summary": list(context.get("input", {}).keys())},
    )
    ApprovalService.emit_requested(approval)
    return approval


class ApprovalService:
    @staticmethod
    def emit_requested(approval: ApprovalRequest):
        publish_domain_event(
            service=Service.APPROVAL,
            event_type=EventType.APPROVAL_REQUESTED,
            organization_id=approval.run.workflow.organization_id,
            aggregate_type="approval",
            aggregate_id=approval.id,
            payload={
                "approval_id": approval.id,
                "title": approval.title,
                "run_id": str(approval.run_id),
                "approver_group": approval.approver_group,
                "due_at": approval.due_at.isoformat() if approval.due_at else None,
            },
        )

    @staticmethod
    def emit_decided(approval: ApprovalRequest, *, actor_id: int):
        publish_domain_event(
            service=Service.APPROVAL,
            event_type=EventType.APPROVAL_DECIDED,
            organization_id=approval.run.workflow.organization_id,
            aggregate_type="approval",
            aggregate_id=approval.id,
            actor_id=actor_id,
            payload={
                "approval_id": approval.id,
                "status": approval.status,
                "title": approval.title,
                "run_id": str(approval.run_id),
            },
        )
