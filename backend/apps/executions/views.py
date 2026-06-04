from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.workflows.models import Workflow

from .models import WorkflowRun
from .serializers import WorkflowRunSerializer
from .tasks import start_workflow_run


class WorkflowRunViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WorkflowRunSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["workflow", "status"]

    def get_queryset(self):
        return WorkflowRun.objects.filter(
            workflow__organization__memberships__user=self.request.user
        ).select_related("triggered_by", "workflow").distinct()


@api_view(["POST"])
@permission_classes([AllowAny])
def trigger_webhook(request, workflow_slug):
    try:
        workflow = Workflow.objects.get(
            slug=workflow_slug,
            status=Workflow.Status.ACTIVE,
            trigger_type=Workflow.TriggerType.WEBHOOK,
        )
    except Workflow.DoesNotExist:
        return Response({"detail": "Webhook not found."}, status=status.HTTP_404_NOT_FOUND)

    secret = workflow.trigger_config.get("secret")
    if secret and request.headers.get("X-Webhook-Secret") != secret:
        return Response({"detail": "Invalid secret."}, status=status.HTTP_403_FORBIDDEN)

    run = start_workflow_run(
        workflow_id=workflow.id,
        triggered_by_id=None,
        input_payload=request.data,
    )
    run.trigger_source = "webhook"
    run.save(update_fields=["trigger_source"])
    return Response(WorkflowRunSerializer(run).data, status=status.HTTP_201_CREATED)
