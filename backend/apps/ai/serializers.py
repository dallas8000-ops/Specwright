from rest_framework import serializers

from .models import AIAssessment, AICopilotMessage


class AIAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAssessment
        fields = (
            "id",
            "case",
            "kind",
            "vertical",
            "result",
            "confidence",
            "model_name",
            "created_at",
        )


class AICopilotMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AICopilotMessage
        fields = ("id", "role", "content", "created_at")


class CopilotRequestSerializer(serializers.Serializer):
    message = serializers.CharField()


class NLIntakeSerializer(serializers.Serializer):
    description = serializers.CharField()
