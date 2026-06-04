from rest_framework import serializers

from .models import AccessReviewSchedule, ComplianceReport


class AccessReviewScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessReviewSchedule
        fields = (
            "id",
            "organization",
            "name",
            "cadence_days",
            "next_review_at",
            "owner",
            "is_active",
        )


class ComplianceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceReport
        fields = (
            "id",
            "report_type",
            "title",
            "period_start",
            "period_end",
            "payload",
            "created_at",
        )


class GenerateReportSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(
        choices=["soc2_audit", "approval_chain"],
        default="soc2_audit",
    )
    period_start = serializers.DateField()
    period_end = serializers.DateField()
