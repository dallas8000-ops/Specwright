from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cases.models import Case
from apps.cases.serializers import CaseSerializer
from apps.organizations.models import Membership

from .models import AIAssessment
from .serializers import (
    AIAssessmentSerializer,
    AICopilotMessageSerializer,
    CopilotRequestSerializer,
    NLIntakeSerializer,
)
from .services import AIService
from .verticals import vertical_config


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def product_config(request):
    membership = request.user.memberships.filter(is_primary=True).select_related("organization").first()
    if not membership:
        membership = request.user.memberships.select_related("organization").first()
    if not membership:
        return Response({"detail": "No organization."}, status=400)
    org = membership.organization
    cfg = vertical_config(org)
    return Response(
        {
            "organization": org.name,
            "product_name": cfg["product_name"],
            "tagline": cfg["tagline"],
            "vertical": cfg["vertical"],
            "enabled_case_types": cfg["case_types"],
            "ai_enabled": True,
            "ai_provider_configured": bool(__import__("django.conf", fromlist=["settings"]).settings.AI_API_KEY),
        }
    )


class AIAssessmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AIAssessmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["case", "kind"]

    def get_queryset(self):
        return AIAssessment.objects.filter(
            organization__memberships__user=self.request.user
        ).distinct()


class AICaseActionsViewSet(viewsets.ViewSet):
    """AI intervention endpoints bound to a case — not a generic chat board."""

    permission_classes = [IsAuthenticated]

    def _get_case(self, pk):
        return Case.objects.filter(
            id=pk,
            organization__memberships__user=self.request.user,
        ).select_related("organization").first()

    @action(detail=True, methods=["post"], url_path="triage")
    def triage(self, request, pk=None):
        case = self._get_case(pk)
        if not case:
            return Response(status=status.HTTP_404_NOT_FOUND)
        assessment = AIService.triage_case(case=case, user=request.user)
        return Response(AIAssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="copilot")
    def copilot(self, request, pk=None):
        case = self._get_case(pk)
        if not case:
            return Response(status=status.HTTP_404_NOT_FOUND)
        ser = CopilotRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        msg = AIService.copilot_turn(case=case, user=request.user, message=ser.validated_data["message"])
        return Response(AICopilotMessageSerializer(msg).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="copilot-history")
    def copilot_history(self, request, pk=None):
        case = self._get_case(pk)
        if not case:
            return Response(status=status.HTTP_404_NOT_FOUND)
        msgs = case.copilot_messages.all()
        return Response(AICopilotMessageSerializer(msgs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def nl_intake(request):
    """Describe the situation in prose — AI structures the case for your vertical product."""
    ser = NLIntakeSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    membership = request.user.memberships.filter(is_primary=True).first()
    if not membership:
        membership = request.user.memberships.first()
    if not membership:
        return Response({"detail": "No organization."}, status=400)

    org = membership.organization
    try:
        extracted = AIService.nl_intake(org=org, user=request.user, natural_language=ser.validated_data["description"])
    except ValueError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    from apps.ai.verticals import get_vertical
    from apps.organizations.models import Department

    dept_slug = get_vertical(org)

    department = Department.objects.filter(organization=org, slug=dept_slug).first()
    if not department:
        return Response({"detail": "Department not configured."}, status=400)

    case = Case.objects.create(
        organization=org,
        department=department,
        case_type=extracted["case_type"],
        title=extracted["title"],
        summary=extracted.get("summary", ""),
        subject_label=extracted.get("subject_label", ""),
        priority=extracted.get("priority", "normal"),
        opened_by=request.user,
        stage=Case.Stage.INTAKE,
    )
    from apps.cases.services import CaseService

    CaseService.emit_opened(case, actor_id=request.user.id)
    assessment = AIService.triage_case(case=case, user=request.user)

    return Response(
        {
            "case": CaseSerializer(case, context={"request": request}).data,
            "ai_triage": AIAssessmentSerializer(assessment).data,
            "extracted": extracted,
        },
        status=status.HTTP_201_CREATED,
    )
