from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DomainEvent
from .serializers import DomainEventSerializer, ServiceHealthSerializer
from .types import Service


class DomainEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Event stream history — SOA observability."""

    serializer_class = DomainEventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["service", "event_type", "organization_id"]

    def get_queryset(self):
        return DomainEvent.objects.filter(
            organization_id__in=self.request.user.memberships.values_list(
                "organization_id", flat=True
            )
        ).distinct()[:200]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def service_registry(request):
    """Service-oriented registry — bounded contexts and their responsibilities."""
    services = [
        {
            "name": Service.CASE,
            "title": "Case Service",
            "responsibility": "Opinionated case lifecycle (intake → post-review)",
            "emits": ["case.opened", "case.stage_advanced"],
            "transport": "domain events + REST",
        },
        {
            "name": Service.EXECUTION,
            "title": "Execution Service",
            "responsibility": "Async playbook runs via Celery workers",
            "emits": ["run.started", "run.status_changed", "run.step_completed"],
            "transport": "domain events + Celery",
        },
        {
            "name": Service.APPROVAL,
            "title": "Approval Service",
            "responsibility": "Human sign-off gates blocking execution",
            "emits": ["approval.requested", "approval.decided"],
            "transport": "domain events + REST",
        },
        {
            "name": Service.INTELLIGENCE,
            "title": "Intelligence Service",
            "responsibility": "Proactive scans, institutional memory",
            "emits": ["alert.created", "insight.refreshed", "intelligence.scan_complete"],
            "transport": "domain events + scheduled tasks",
        },
        {
            "name": Service.AI,
            "title": "AI Intervention Service",
            "responsibility": "Triage, copilot, NL intake — vertical-specific LLM prompts",
            "emits": ["ai.assessment_complete"],
            "transport": "domain events + OpenAI-compatible API",
        },
        {
            "name": Service.INTEGRATION,
            "title": "Integration Service",
            "responsibility": "Outbound connectors (REST, Slack, …)",
            "emits": ["integration.completed"],
            "transport": "domain events",
        },
    ]
    return Response(
        {
            "architecture": "event-driven service-oriented",
            "realtime": "WebSocket /ws/ops/ (JWT)",
            "async_workers": "Celery + Redis",
            "services": services,
        }
    )
