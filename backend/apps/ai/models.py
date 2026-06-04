from django.conf import settings
from django.db import models


class AIAssessment(models.Model):
    """Persisted AI intervention — auditable, not ephemeral chat-only."""

    class AssessmentKind(models.TextChoices):
        TRIAGE = "triage", "Case Triage"
        COPILOT = "copilot", "Copilot Turn"
        RISK_SCAN = "risk_scan", "Risk Scan"
        DRAFT = "draft", "Draft Communication"

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, related_name="ai_assessments"
    )
    case = models.ForeignKey(
        "cases.Case",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_assessments",
    )
    kind = models.CharField(max_length=32, choices=AssessmentKind.choices)
    vertical = models.CharField(max_length=32)
    prompt_snapshot = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    confidence = models.FloatField(default=0)
    model_name = models.CharField(max_length=64, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ai_assessments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AICopilotMessage(models.Model):
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, related_name="copilot_messages")
    role = models.CharField(max_length=16)  # user | assistant
    content = models.TextField()
    assessment = models.ForeignKey(
        AIAssessment, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
