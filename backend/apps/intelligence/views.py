from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.services import log_action
from apps.events.bus import publish_domain_event
from apps.events.types import EventType, Service
from apps.integrations.slack_actions import send_slack_actionable_alert

from .models import MemoryInsight, ProactiveAlert
from .serializers import MemoryInsightSerializer, ProactiveAlertSerializer
from .services import refresh_institutional_memory, scan_proactive_alerts


class MemoryInsightViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MemoryInsightSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["kind", "severity"]

    def get_queryset(self):
        return MemoryInsight.objects.filter(
            organization__memberships__user=self.request.user
        ).distinct()


class ProactiveAlertViewSet(viewsets.ModelViewSet):
    serializer_class = ProactiveAlertSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "post", "head", "options"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["kind", "severity", "acknowledged"]

    def get_queryset(self):
        return ProactiveAlert.objects.filter(
            organization__memberships__user=self.request.user
        ).distinct()

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.acknowledged = True
        alert.save(update_fields=["acknowledged"])
        publish_domain_event(
            service=Service.INTELLIGENCE,
            event_type=EventType.ALERT_ACKNOWLEDGED,
            organization_id=alert.organization_id,
            aggregate_type="alert",
            aggregate_id=alert.id,
            actor_id=request.user.id,
            payload={"alert_id": alert.id, "title": alert.title},
        )
        log_action(action="update", resource_type="alert", resource_id=alert.id, metadata={"acknowledged": True})
        return Response(ProactiveAlertSerializer(alert).data)

    @action(detail=True, methods=["post"])
    def escalate(self, request, pk=None):
        alert = self.get_object()
        alert.escalated = True
        alert.save(update_fields=["escalated"])
        send_slack_actionable_alert(alert, action="escalated")
        log_action(action="update", resource_type="alert", resource_id=alert.id, metadata={"escalated": True})
        return Response(ProactiveAlertSerializer(alert).data)

    @action(detail=False, methods=["post"], url_path="refresh-scan")
    def refresh_scan(self, request):
        membership = request.user.memberships.filter(is_primary=True).first()
        if not membership:
            membership = request.user.memberships.first()
        if not membership:
            return Response({"detail": "No organization."}, status=400)
        org = membership.organization
        refresh_institutional_memory(org)
        scan_proactive_alerts(org)
        publish_domain_event(
            service=Service.INTELLIGENCE,
            event_type=EventType.INTELLIGENCE_SCAN_COMPLETE,
            organization_id=org.id,
            actor_id=request.user.id,
            payload={"organization": org.slug},
        )
        return Response({"status": "scan_complete"}, status=status.HTTP_200_OK)
