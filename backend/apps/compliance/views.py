from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import json

from apps.audit.services import log_action
from apps.organizations.models import Membership

from .models import AccessReviewSchedule, ComplianceReport
from .serializers import (
    AccessReviewScheduleSerializer,
    ComplianceReportSerializer,
    GenerateReportSerializer,
)
from .services import generate_approval_chain_report, generate_soc2_audit_report


class ComplianceReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ComplianceReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ComplianceReport.objects.filter(
            organization__memberships__user=self.request.user
        ).distinct()

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        ser = GenerateReportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        membership = request.user.memberships.filter(is_primary=True).first()
        if not membership:
            membership = request.user.memberships.first()
        if not membership:
            return Response({"detail": "No organization."}, status=400)

        if ser.validated_data["report_type"] == "soc2_audit":
            report = generate_soc2_audit_report(
                membership.organization,
                period_start=ser.validated_data["period_start"],
                period_end=ser.validated_data["period_end"],
                generated_by=request.user,
            )
        else:
            report = generate_approval_chain_report(
                membership.organization,
                period_start=ser.validated_data["period_start"],
                period_end=ser.validated_data["period_end"],
                generated_by=request.user,
            )

        log_action(
            action="export",
            resource_type="compliance_report",
            resource_id=report.id,
            metadata={"report_type": report.report_type},
        )
        return Response(ComplianceReportSerializer(report).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="export")
    def export(self, request, pk=None):
        report = self.get_object()
        content = json.dumps(report.payload, indent=2)
        response = HttpResponse(content, content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="{report.title}.json"'
        return response


class AccessReviewScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccessReviewScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AccessReviewSchedule.objects.filter(
            organization__memberships__user=self.request.user,
            is_active=True,
        ).distinct()
