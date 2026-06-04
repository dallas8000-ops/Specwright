from django.conf import settings
from django.db import models

from apps.executions.models import WorkflowRun


class ApprovalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        ESCALATED = "escalated", "Escalated"
        EXPIRED = "expired", "Expired"

    run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE, related_name="approvals")
    node_key = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_approvals",
    )
    approver_group = models.CharField(max_length=128, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decided_approvals",
    )
    decision_note = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
