from rest_framework import serializers

from apps.context.meaning import alert_meaning, insight_meaning

from .models import MemoryInsight, ProactiveAlert


class MemoryInsightSerializer(serializers.ModelSerializer):
    meaning = serializers.SerializerMethodField()

    class Meta:
        model = MemoryInsight
        fields = (
            "id",
            "kind",
            "title",
            "detail",
            "subject_key",
            "occurrence_count",
            "severity",
            "metadata",
            "first_seen",
            "last_seen",
            "meaning",
        )

    def get_meaning(self, obj) -> dict:
        return insight_meaning(obj)


class ProactiveAlertSerializer(serializers.ModelSerializer):
    meaning = serializers.SerializerMethodField()

    class Meta:
        model = ProactiveAlert
        fields = (
            "id",
            "kind",
            "title",
            "message",
            "severity",
            "subject_key",
            "acknowledged",
            "escalated",
            "created_at",
            "meaning",
        )

    def get_meaning(self, obj) -> dict:
        return alert_meaning(obj)
