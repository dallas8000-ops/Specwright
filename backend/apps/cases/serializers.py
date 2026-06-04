from rest_framework import serializers

from apps.context.meaning import case_meaning

from .models import Case


class CaseSerializer(serializers.ModelSerializer):
    case_type_label = serializers.CharField(source="get_case_type_display", read_only=True)
    stage_label = serializers.CharField(source="get_stage_display", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    opened_by_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    next_stage = serializers.SerializerMethodField()
    meaning = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = (
            "id",
            "organization",
            "department",
            "department_name",
            "case_type",
            "case_type_label",
            "stage",
            "stage_label",
            "next_stage",
            "title",
            "summary",
            "subject_key",
            "subject_label",
            "priority",
            "assigned_to",
            "assigned_to_name",
            "opened_by",
            "opened_by_name",
            "meaning",
            "workflow_run_id",
            "resolved_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "stage", "resolved_at", "opened_by", "created_at", "updated_at")

    def get_opened_by_name(self, obj: Case) -> str:
        if not obj.opened_by:
            return ""
        return obj.opened_by.get_full_name() or obj.opened_by.username

    def get_assigned_to_name(self, obj: Case) -> str:
        if not obj.assigned_to:
            return ""
        return obj.assigned_to.get_full_name() or obj.assigned_to.username

    def get_meaning(self, obj: Case) -> dict:
        request = self.context.get("request")
        viewer = request.user.username if request and request.user.is_authenticated else ""
        return case_meaning(obj, viewer_username=viewer)

    def get_next_stage(self, obj: Case) -> str | None:
        try:
            idx = Case.STAGE_ORDER.index(obj.stage)
            if idx < len(Case.STAGE_ORDER) - 1:
                return Case.STAGE_ORDER[idx + 1]
        except ValueError:
            pass
        return None

    def create(self, validated_data):
        validated_data["opened_by"] = self.context["request"].user
        validated_data["stage"] = Case.Stage.INTAKE
        return super().create(validated_data)


class QuickOpenCaseSerializer(serializers.Serializer):
    """Ruthless simplicity — open a case in one POST."""

    case_type = serializers.ChoiceField(choices=Case.CaseType.choices)
    title = serializers.CharField(max_length=255)
    subject_label = serializers.CharField(max_length=255, required=False, allow_blank=True)
    summary = serializers.CharField(required=False, allow_blank=True)
