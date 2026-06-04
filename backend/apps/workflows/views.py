from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.views import CurrentUserMixin
from apps.executions.tasks import start_workflow_run

from .models import Workflow, WorkflowTemplate
from .serializers import (
    WorkflowSerializer,
    WorkflowTemplateSerializer,
    WorkflowWriteSerializer,
)


class WorkflowViewSet(CurrentUserMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["organization", "department", "status", "trigger_type"]
    lookup_field = "slug"

    def get_queryset(self):
        return Workflow.objects.filter(
            organization__memberships__user=self.request.user
        ).distinct()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return WorkflowWriteSerializer
        return WorkflowSerializer

    @action(detail=True, methods=["post"])
    def publish(self, request, slug=None):
        workflow = self.get_object()
        workflow.status = Workflow.Status.ACTIVE
        workflow.save(update_fields=["status"])
        return Response(WorkflowSerializer(workflow).data)

    @action(detail=True, methods=["post"])
    def run(self, request, slug=None):
        workflow = self.get_object()
        if workflow.status != Workflow.Status.ACTIVE:
            return Response(
                {"detail": "Workflow must be active to run."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        run = start_workflow_run(
            workflow_id=workflow.id,
            triggered_by_id=request.user.id,
            input_payload=request.data.get("input", {}),
        )
        from apps.executions.serializers import WorkflowRunSerializer

        return Response(WorkflowRunSerializer(run).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def export(self, request, slug=None):
        workflow = self.get_object()
        nodes = [
            {
                "key": n.key,
                "type": n.node_type,
                "label": n.label,
                "config": n.config,
                "x": n.position_x,
                "y": n.position_y,
            }
            for n in workflow.nodes.all()
        ]
        edges = [
            {"source": e.source.key, "target": e.target.key, "label": e.label}
            for e in workflow.edges.all()
        ]
        return Response({"nodes": nodes, "edges": edges})


class WorkflowTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowTemplate.objects.filter(is_public=True)
    serializer_class = WorkflowTemplateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"
