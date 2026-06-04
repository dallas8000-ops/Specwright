from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        RUN = "run", "Run"
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"
        LOGIN = "login", "Login"
        EXPORT = "export", "Export"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    resource_type = models.CharField(max_length=64)
    resource_id = models.CharField(max_length=64)
    organization_id = models.IntegerField(null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
