from django.db import models


class DomainEvent(models.Model):
    """Persisted event log — SOA audit trail + replay source."""

    service = models.CharField(max_length=64, db_index=True)
    event_type = models.CharField(max_length=64, db_index=True)
    organization_id = models.IntegerField(null=True, blank=True, db_index=True)
    aggregate_type = models.CharField(max_length=64, blank=True)
    aggregate_id = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict)
    correlation_id = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization_id", "event_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.service}:{self.event_type}"
