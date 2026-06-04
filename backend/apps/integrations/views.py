from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Connector, Credential
from .serializers import ConnectorSerializer, CredentialSerializer
from .slack_actions import handle_slack_interaction


class ConnectorViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ConnectorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["kind", "organization"]
    lookup_field = "slug"

    def get_queryset(self):
        return Connector.objects.filter(is_active=True)


class CredentialViewSet(viewsets.ModelViewSet):
    serializer_class = CredentialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["organization", "connector"]

    def get_queryset(self):
        return Credential.objects.filter(
            organization__memberships__user=self.request.user
        ).distinct()


@api_view(["POST"])
@permission_classes([AllowAny])
def slack_interaction(request):
    """Slack interactive buttons: Acknowledge / Escalate proactive alerts."""
    payload = request.data.get("payload") or request.data
    if isinstance(payload, str):
        import json

        payload = json.loads(payload)
    result = handle_slack_interaction(payload if isinstance(payload, dict) else request.data)
    return Response(result)
