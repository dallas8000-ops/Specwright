from rest_framework import serializers

from apps.context.meaning import run_meaning

from .models import StepRun, WorkflowRun


class StepRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepRun
        fields = (
            "id",
            "node_key",
            "node_type",
            "status",
            "attempt",
            "output",
            "error_message",
            "started_at",
            "finished_at",
        )


class WorkflowRunSerializer(serializers.ModelSerializer):
    steps = StepRunSerializer(many=True, read_only=True)
    workflow_name = serializers.CharField(source="workflow.name", read_only=True)
    workflow_slug = serializers.CharField(source="workflow.slug", read_only=True)
    triggered_by_name = serializers.SerializerMethodField()
    meaning = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowRun
        fields = (
            "id",
            "workflow",
            "workflow_name",
            "workflow_slug",
            "status",
            "triggered_by",
            "triggered_by_name",
            "meaning",
            "trigger_source",
            "context",
            "error_message",
            "sla_deadline",
            "steps",
            "started_at",
            "finished_at",
        )

    def get_triggered_by_name(self, obj) -> str:
        if not obj.triggered_by:
            return ""
        return obj.triggered_by.get_full_name() or obj.triggered_by.username

    def get_meaning(self, obj) -> dict:
        return run_meaning(obj)
