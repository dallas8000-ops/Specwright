import uuid

from django.conf import settings
from django.db import models

from apps.workflows.models import Workflow


class WorkflowRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        WAITING = "waiting", "Waiting"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_runs",
    )
    trigger_source = models.CharField(max_length=64, default="manual")
    context = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    sla_deadline = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.workflow.slug} — {self.id}"


class StepRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        WAITING = "waiting", "Waiting"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        SKIPPED = "skipped", "Skipped"

    run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE, related_name="steps")
    node_key = models.CharField(max_length=64)
    node_type = models.CharField(max_length=32)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    attempt = models.PositiveIntegerField(default=1)
    input_data = models.JSONField(default=dict, blank=True)
    output = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("run", "node_key", "attempt")]
        ordering = ["started_at"]
