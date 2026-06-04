from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.organizations.models import Department, Organization


class Case(models.Model):
    """
    Opinionated ops case — not a generic record.
    Stages are enforced: Intake → Investigation → Resolution → Post-review.
    """

    class CaseType(models.TextChoices):
        NEW_HIRE = "new_hire", "New Hire Request"
        POLICY_EXCEPTION = "policy_exception", "Policy Exception"
        CONTRACT_REVIEW = "contract_review", "Contract Review"
        SHIPMENT_EXCEPTION = "shipment_exception", "Shipment Exception"
        ACCESS_REVIEW = "access_review", "Access Review"

    class Stage(models.TextChoices):
        INTAKE = "intake", "Intake"
        INVESTIGATION = "investigation", "Investigation"
        RESOLUTION = "resolution", "Resolution"
        POST_REVIEW = "post_review", "Post-Review"

    STAGE_ORDER = [
        Stage.INTAKE,
        Stage.INVESTIGATION,
        Stage.RESOLUTION,
        Stage.POST_REVIEW,
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="cases")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="cases")
    case_type = models.CharField(max_length=32, choices=CaseType.choices)
    stage = models.CharField(max_length=32, choices=Stage.choices, default=Stage.INTAKE)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    # Institutional memory anchor — tie cases to real business entities
    subject_key = models.CharField(max_length=128, blank=True, help_text="e.g. employee:E1024")
    subject_label = models.CharField(max_length=255, blank=True)
    priority = models.CharField(
        max_length=16,
        choices=[("low", "Low"), ("normal", "Normal"), ("high", "High"), ("critical", "Critical")],
        default="normal",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cases",
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="opened_cases",
    )
    workflow_run_id = models.UUIDField(null=True, blank=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.get_case_type_display()} — {self.title}"

    def advance_stage(self):
        idx = self.STAGE_ORDER.index(self.stage)
        if idx >= len(self.STAGE_ORDER) - 1:
            raise ValidationError("Case is already in final stage.")
        self.stage = self.STAGE_ORDER[idx + 1]
        if self.stage == self.Stage.POST_REVIEW:
            from django.utils import timezone

            self.resolved_at = timezone.now()

    def clean(self):
        if self.department_id and self.organization_id:
            if self.department.organization_id != self.organization_id:
                raise ValidationError("Department must belong to the case organization.")
