from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class MemoryInsight(models.Model):
    """Institutional memory — patterns the app surfaces proactively."""

    class InsightKind(models.TextChoices):
        RECURRING_ISSUE = "recurring_issue", "Recurring Issue"
        STALE_ACCESS = "stale_access", "Stale Access"
        SLA_RISK = "sla_risk", "SLA At Risk"
        ENTITY_HISTORY = "entity_history", "Entity History"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="insights"
    )
    kind = models.CharField(max_length=32, choices=InsightKind.choices)
    title = models.CharField(max_length=255)
    detail = models.TextField()
    subject_key = models.CharField(max_length=128, blank=True, db_index=True)
    occurrence_count = models.PositiveIntegerField(default=1)
    severity = models.CharField(
        max_length=16,
        choices=[("info", "Info"), ("warning", "Warning"), ("critical", "Critical")],
        default="info",
    )
    metadata = models.JSONField(default=dict, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen"]


class ProactiveAlert(models.Model):
    """What's about to go wrong — not just what already failed."""

    class AlertKind(models.TextChoices):
        SLA_BREACH = "sla_breach", "SLA Breach Imminent"
        APPROVAL_OVERDUE = "approval_overdue", "Approval Overdue"
        CASE_STUCK = "case_stuck", "Case Stuck in Stage"
        INTEGRATION_FAILURE = "integration_failure", "Integration Failure Spike"
        ACCESS_REVIEW_DUE = "access_review_due", "Access Review Due"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="alerts"
    )
    kind = models.CharField(max_length=32, choices=AlertKind.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    severity = models.CharField(max_length=16, default="warning")
    subject_key = models.CharField(max_length=128, blank=True)
    acknowledged = models.BooleanField(default=False)
    escalated = models.BooleanField(default=False)
    slack_message_ts = models.CharField(max_length=64, blank=True)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="proactive_alerts",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
