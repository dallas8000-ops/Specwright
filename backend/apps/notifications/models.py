from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Channel(models.TextChoices):
        IN_APP = "in_app", "In-App"
        EMAIL = "email", "Email"
        SLACK = "slack", "Slack"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    channel = models.CharField(max_length=16, choices=Channel.choices, default=Channel.IN_APP)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.NORMAL)
    link = models.CharField(max_length=512, blank=True)
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
