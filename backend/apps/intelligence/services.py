from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from apps.approvals.models import ApprovalRequest
from apps.cases.models import Case
from apps.executions.models import WorkflowRun
from apps.organizations.models import Organization

from apps.events.bus import publish_domain_event
from apps.events.types import EventType, Service

from .models import MemoryInsight, ProactiveAlert

User = get_user_model()


def refresh_institutional_memory(organization: Organization):
    """Scan recent activity and upsert memory insights."""
    since = timezone.now() - timedelta(days=30)
    failed_by_workflow = (
        WorkflowRun.objects.filter(
            workflow__organization=organization,
            status=WorkflowRun.Status.FAILED,
            started_at__gte=since,
        )
        .values("workflow__slug")
        .annotate(count=Count("id"))
        .filter(count__gte=3)
    )
    for row in failed_by_workflow:
        slug = row["workflow__slug"]
        MemoryInsight.objects.update_or_create(
            organization=organization,
            kind=MemoryInsight.InsightKind.RECURRING_ISSUE,
            subject_key=f"workflow:{slug}",
            defaults={
                "title": f"Workflow '{slug}' failed {row['count']} times in 30 days",
                "detail": "Consider a post-review or process change — this pattern is recurring.",
                "occurrence_count": row["count"],
                "severity": "warning" if row["count"] < 5 else "critical",
            },
        )

    stale_users = User.objects.filter(
        memberships__organization=organization,
        last_login__lt=timezone.now() - timedelta(days=60),
    )[:10]
    for u in stale_users:
        MemoryInsight.objects.update_or_create(
            organization=organization,
            kind=MemoryInsight.InsightKind.STALE_ACCESS,
            subject_key=f"user:{u.id}",
            defaults={
                "title": f"{u.get_full_name() or u.username} inactive 60+ days",
                "detail": "Schedule an access review — dormant accounts are a compliance risk.",
                "severity": "warning",
                "metadata": {"username": u.username, "email": u.email},
            },
        )


def scan_proactive_alerts(organization: Organization):
    now = timezone.now()
    overdue = ApprovalRequest.objects.filter(
        run__workflow__organization=organization,
        status=ApprovalRequest.Status.PENDING,
        due_at__lt=now,
    )
    for approval in overdue[:20]:
        alert, created = ProactiveAlert.objects.get_or_create(
            organization=organization,
            kind=ProactiveAlert.AlertKind.APPROVAL_OVERDUE,
            title=f"Overdue: {approval.title}",
            defaults={
                "message": f"Approval pending past due since {approval.due_at}. Escalate or decide now.",
                "severity": "critical",
                "subject_key": f"approval:{approval.id}",
                "recipient": approval.assigned_to,
            },
        )
        if created:
            publish_domain_event(
                service=Service.INTELLIGENCE,
                event_type=EventType.ALERT_CREATED,
                organization_id=organization.id,
                aggregate_type="alert",
                aggregate_id=alert.id,
                payload={"alert_id": alert.id, "title": alert.title, "kind": alert.kind},
            )

    stuck_cases = Case.objects.filter(
        organization=organization,
        updated_at__lt=now - timedelta(days=3),
        stage__in=[Case.Stage.INVESTIGATION, Case.Stage.RESOLUTION],
        resolved_at__isnull=True,
    )
    for case in stuck_cases[:20]:
        ProactiveAlert.objects.get_or_create(
            organization=organization,
            kind=ProactiveAlert.AlertKind.CASE_STUCK,
            title=f"Case stuck: {case.title}",
            defaults={
                "message": f"In '{case.get_stage_display()}' for 3+ days. Advance or reassign.",
                "severity": "warning",
                "subject_key": f"case:{case.id}",
                "recipient": case.assigned_to,
            },
        )

    at_risk = WorkflowRun.objects.filter(
        workflow__organization=organization,
        status__in=[WorkflowRun.Status.RUNNING, WorkflowRun.Status.WAITING],
        sla_deadline__lte=now + timedelta(hours=4),
        sla_deadline__gte=now,
    )
    for run in at_risk[:20]:
        ProactiveAlert.objects.get_or_create(
            organization=organization,
            kind=ProactiveAlert.AlertKind.SLA_BREACH,
            title=f"SLA at risk: {run.workflow.name}",
            defaults={
                "message": f"Run {str(run.id)[:8]} hits SLA in under 4 hours.",
                "severity": "warning",
                "subject_key": f"run:{run.id}",
            },
        )
