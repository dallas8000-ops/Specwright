from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.executions.tasks import resume_workflow_run

from .models import ApprovalRequest
from .services import ApprovalService
from .serializers import ApprovalDecisionSerializer, ApprovalRequestSerializer


class ApprovalRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "run"]

    def get_queryset(self):
        return ApprovalRequest.objects.filter(
            run__workflow__organization__memberships__user=self.request.user
        ).select_related("assigned_to", "decided_by", "run__workflow").distinct()

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        approval = self.get_object()
        if approval.status != ApprovalRequest.Status.PENDING:
            return Response(
                {"detail": "Already decided."}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approved = serializer.validated_data["approved"]
        approval.status = (
            ApprovalRequest.Status.APPROVED if approved else ApprovalRequest.Status.REJECTED
        )
        approval.decided_by = request.user
        approval.decision_note = serializer.validated_data.get("note", "")
        approval.decided_at = timezone.now()
        approval.save()

        ApprovalService.emit_decided(approval, actor_id=request.user.id)

        if approved:
            resume_workflow_run.delay(str(approval.run_id), approval.node_key)
        else:
            approval.run.status = approval.run.Status.FAILED
            approval.run.error_message = "Approval rejected"
            approval.run.finished_at = timezone.now()
            approval.run.save()

        return Response(ApprovalRequestSerializer(approval).data)
