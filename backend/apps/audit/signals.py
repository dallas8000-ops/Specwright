"""Audit trails are automatic — users never toggle logging on."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.approvals.models import ApprovalRequest
from apps.cases.models import Case
from apps.executions.models import WorkflowRun
from apps.workflows.models import Workflow

from .services import log_action


@receiver(post_save, sender=Workflow)
def audit_workflow_save(sender, instance, created, **kwargs):
    log_action(
        action="create" if created else "update",
        resource_type="workflow",
        resource_id=instance.id,
        metadata={"slug": instance.slug, "status": instance.status},
    )


@receiver(post_save, sender=WorkflowRun)
def audit_run_save(sender, instance, created, **kwargs):
    if created or instance.status in (WorkflowRun.Status.COMPLETED, WorkflowRun.Status.FAILED):
        log_action(
            action="run",
            resource_type="workflow_run",
            resource_id=instance.id,
            metadata={"status": instance.status, "workflow": instance.workflow.slug},
        )


@receiver(post_save, sender=ApprovalRequest)
def audit_approval_save(sender, instance, **kwargs):
    if instance.status != ApprovalRequest.Status.PENDING and instance.decided_at:
        log_action(
            action="approve" if instance.status == ApprovalRequest.Status.APPROVED else "reject",
            resource_type="approval",
            resource_id=instance.id,
            metadata={"title": instance.title, "run_id": str(instance.run_id)},
        )


@receiver(post_save, sender=Case)
def audit_case_save(sender, instance, created, **kwargs):
    log_action(
        action="create" if created else "update",
        resource_type="case",
        resource_id=instance.id,
        metadata={"case_type": instance.case_type, "stage": instance.stage},
    )
