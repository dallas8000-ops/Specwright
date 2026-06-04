from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class Connector(models.Model):
    """Built-in and custom integration types (REST, email, Slack, SAP, etc.)."""

    class ConnectorKind(models.TextChoices):
        REST = "rest", "REST API"
        WEBHOOK_OUT = "webhook_out", "Outbound Webhook"
        EMAIL = "email", "Email"
        SLACK = "slack", "Slack"
        TEAMS = "teams", "Microsoft Teams"
        GOOGLE_SHEETS = "google_sheets", "Google Sheets"
        SHAREPOINT = "sharepoint", "SharePoint"
        SAP = "sap", "SAP"
        WORKDAY = "workday", "Workday"
        DOCUSIGN = "docusign", "DocuSign"
        CUSTOM = "custom", "Custom Script"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="connectors",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    kind = models.CharField(max_length=32, choices=ConnectorKind.choices)
    description = models.TextField(blank=True)
    config_schema = models.JSONField(default=dict)
    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("organization", "slug")]

    def __str__(self):
        return self.name


class Credential(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="credentials"
    )
    connector = models.ForeignKey(Connector, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    encrypted_secrets = models.BinaryField()
    metadata = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.connector.name})"


class IntegrationLog(models.Model):
    run_id = models.UUIDField(db_index=True, null=True, blank=True)
    connector = models.ForeignKey(Connector, on_delete=models.CASCADE)
    request_summary = models.JSONField(default=dict)
    response_summary = models.JSONField(default=dict)
    status_code = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=False)
    duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
