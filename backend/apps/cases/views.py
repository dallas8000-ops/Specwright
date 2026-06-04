from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.services import log_action
from apps.organizations.models import Department, Membership

from apps.ai.services import AIService

from .models import Case
from .services import CaseService
from .serializers import CaseSerializer, QuickOpenCaseSerializer


class CaseViewSet(viewsets.ModelViewSet):
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["department", "case_type", "stage", "priority"]

    def get_queryset(self):
        return Case.objects.filter(
            organization__memberships__user=self.request.user
        ).select_related("opened_by", "assigned_to", "department").distinct()

    def perform_create(self, serializer):
        org = serializer.validated_data["organization"]
        try:
            AIService.assert_case_allowed(org, serializer.validated_data["case_type"])
        except ValueError as e:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(str(e)) from e
        case = serializer.save()
        CaseService.emit_opened(case, actor_id=self.request.user.id)
        log_action(
            action="create",
            resource_type="case",
            resource_id=case.id,
            metadata={"case_type": case.case_type, "stage": case.stage},
        )

    @action(detail=False, methods=["post"], url_path="quick-open")
    def quick_open(self, request):
        """Under 2 minutes: file first hire request, contract, or shipment exception."""
        ser = QuickOpenCaseSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        membership = Membership.objects.filter(user=request.user, is_primary=True).first()
        if not membership:
            membership = Membership.objects.filter(user=request.user).first()
        if not membership:
            return Response(
                {"detail": "No organization membership. Contact your admin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dept_map = {
            Case.CaseType.NEW_HIRE: "hr",
            Case.CaseType.POLICY_EXCEPTION: "hr",
            Case.CaseType.CONTRACT_REVIEW: "legal",
            Case.CaseType.SHIPMENT_EXCEPTION: "logistics",
            Case.CaseType.ACCESS_REVIEW: "hr",
        }
        dept_slug = dept_map.get(ser.validated_data["case_type"], "hr")
        department = Department.objects.filter(
            organization=membership.organization, slug=dept_slug
        ).first()
        if not department:
            return Response({"detail": "Department not configured."}, status=400)

        try:
            AIService.assert_case_allowed(membership.organization, ser.validated_data["case_type"])
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        case = Case.objects.create(
            organization=membership.organization,
            department=department,
            case_type=ser.validated_data["case_type"],
            title=ser.validated_data["title"],
            summary=ser.validated_data.get("summary", ""),
            subject_label=ser.validated_data.get("subject_label", ""),
            opened_by=request.user,
            stage=Case.Stage.INTAKE,
        )
        log_action(action="create", resource_type="case", resource_id=case.id, metadata={"quick_open": True})
        CaseService.emit_opened(case, actor_id=request.user.id)
        return Response(CaseSerializer(case, context={"request": request}).data, status=201)

    @action(detail=True, methods=["post"])
    def advance(self, request, pk=None):
        case = self.get_object()
        try:
            case.advance_stage()
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        case.save()
        log_action(
            action="update",
            resource_type="case",
            resource_id=case.id,
            metadata={"stage": case.stage, "advanced": True},
        )
        CaseService.emit_stage_advanced(case, actor_id=request.user.id)
        return Response(CaseSerializer(case).data)
