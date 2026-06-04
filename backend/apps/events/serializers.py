from rest_framework import serializers

from .models import DomainEvent


class DomainEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainEvent
        fields = (
            "id",
            "service",
            "event_type",
            "organization_id",
            "aggregate_type",
            "aggregate_id",
            "payload",
            "correlation_id",
            "created_at",
        )


class ServiceHealthSerializer(serializers.Serializer):
    name = serializers.CharField()
    status = serializers.CharField()
