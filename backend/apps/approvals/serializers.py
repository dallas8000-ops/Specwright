from rest_framework import serializers

from apps.context.meaning import approval_meaning

from .models import ApprovalRequest


class ApprovalRequestSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source="run.workflow.name", read_only=True)
    run_id = serializers.UUIDField(source="run.id", read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    decided_by_name = serializers.SerializerMethodField()
    meaning = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalRequest
        fields = (
            "id",
            "run",
            "run_id",
            "workflow_name",
            "node_key",
            "title",
            "description",
            "status",
            "assigned_to",
            "assigned_to_name",
            "approver_group",
            "due_at",
            "decided_by",
            "decided_by_name",
            "meaning",
            "decision_note",
            "payload",
            "created_at",
            "decided_at",
        )
        read_only_fields = ("id", "created_at", "decided_at", "decided_by")

    def get_assigned_to_name(self, obj) -> str:
        if not obj.assigned_to:
            return ""
        return obj.assigned_to.get_full_name() or obj.assigned_to.username

    def get_decided_by_name(self, obj) -> str:
        if not obj.decided_by:
            return ""
        return obj.decided_by.username

    def get_meaning(self, obj) -> dict:
        return approval_meaning(obj)


class ApprovalDecisionSerializer(serializers.Serializer):
    approved = serializers.BooleanField()
    note = serializers.CharField(required=False, allow_blank=True)
