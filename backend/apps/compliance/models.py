from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class AccessReviewSchedule(models.Model):
    """Compliance-ready: scheduled user access reviews."""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="access_reviews"
    )
    name = models.CharField(max_length=255)
    cadence_days = models.PositiveIntegerField(default=90)
    next_review_at = models.DateField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_access_reviews",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["next_review_at"]


class ComplianceReport(models.Model):
    class ReportType(models.TextChoices):
        SOC2_AUDIT = "soc2_audit", "SOC 2 Audit Trail"
        HIPAA_ACCESS = "hipaa_access", "HIPAA Access Log"
        APPROVAL_CHAIN = "approval_chain", "Approval Chain Evidence"
        USER_ACCESS = "user_access", "User Access Review"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="compliance_reports"
    )
    report_type = models.CharField(max_length=32, choices=ReportType.choices)
    title = models.CharField(max_length=255)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    period_start = models.DateField()
    period_end = models.DateField()
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
