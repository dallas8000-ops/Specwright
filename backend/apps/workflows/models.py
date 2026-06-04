from django.conf import settings
from django.db import models

from apps.organizations.models import Department, Organization


class WorkflowTemplate(models.Model):
    """Pre-built flows for HR onboarding, contract review, shipment routing, etc."""

    class Category(models.TextChoices):
        HR = "hr", "HR"
        LEGAL = "legal", "Legal"
        LOGISTICS = "logistics", "Logistics"
        FINANCE = "finance", "Finance"
        GENERAL = "general", "General"

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=32, choices=Category.choices)
    description = models.TextField(blank=True)
    definition = models.JSONField(default=dict)
    variables_schema = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Workflow(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"

    class TriggerType(models.TextChoices):
        MANUAL = "manual", "Manual"
        SCHEDULE = "schedule", "Schedule"
        WEBHOOK = "webhook", "Webhook"
        EVENT = "event", "Internal Event"
        FORM = "form", "Form Submission"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="workflows"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflows",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    trigger_type = models.CharField(
        max_length=16, choices=TriggerType.choices, default=TriggerType.MANUAL
    )
    trigger_config = models.JSONField(default=dict, blank=True)
    variables_schema = models.JSONField(default=dict, blank=True)
    sla_hours = models.PositiveIntegerField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    template = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instances",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_workflows",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("organization", "slug")]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} v{self.version}"


class WorkflowNode(models.Model):
    class NodeType(models.TextChoices):
        TRIGGER = "trigger", "Trigger"
        ACTION = "action", "Action"
        CONDITION = "condition", "Condition"
        APPROVAL = "approval", "Approval"
        DELAY = "delay", "Delay"
        PARALLEL = "parallel", "Parallel Split"
        JOIN = "join", "Join"
        TRANSFORM = "transform", "Data Transform"
        NOTIFICATION = "notification", "Notification"
        INTEGRATION = "integration", "Integration Call"
        HUMAN_TASK = "human_task", "Human Task"
        SUBFLOW = "subflow", "Sub-workflow"

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="nodes")
    key = models.CharField(max_length=64)
    node_type = models.CharField(max_length=32, choices=NodeType.choices)
    label = models.CharField(max_length=255)
    config = models.JSONField(default=dict)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    retry_policy = models.JSONField(default=dict, blank=True)
    timeout_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = [("workflow", "key")]
        ordering = ["key"]

    def __str__(self):
        return f"{self.workflow.slug}:{self.key}"


class WorkflowEdge(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="edges")
    source = models.ForeignKey(
        WorkflowNode, on_delete=models.CASCADE, related_name="outgoing"
    )
    target = models.ForeignKey(
        WorkflowNode, on_delete=models.CASCADE, related_name="incoming"
    )
    condition = models.JSONField(default=dict, blank=True)
    label = models.CharField(max_length=128, blank=True)

    class Meta:
        unique_together = [("workflow", "source", "target")]


class WorkflowVersion(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    snapshot = models.JSONField()
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    published_at = models.DateTimeField(auto_now_add=True)
    changelog = models.TextField(blank=True)

    class Meta:
        unique_together = [("workflow", "version_number")]
        ordering = ["-version_number"]
