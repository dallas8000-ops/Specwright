from django.contrib.auth import get_user_model

from apps.approvals.models import ApprovalRequest
from apps.audit.models import AuditLog

from .models import ComplianceReport

User = get_user_model()


def generate_soc2_audit_report(organization, *, period_start, period_end, generated_by):
    logs = AuditLog.objects.filter(
        organization_id=organization.id,
        created_at__date__gte=period_start,
        created_at__date__lte=period_end,
    ).order_by("created_at")

    entries = [
        {
            "timestamp": log.created_at.isoformat(),
            "actor": log.actor.username if log.actor else "system",
            "action": log.action,
            "resource": f"{log.resource_type}:{log.resource_id}",
            "ip": log.ip_address,
            "metadata": log.metadata,
        }
        for log in logs[:5000]
    ]

    payload = {
        "framework": "SOC2",
        "control_family": "CC6 - Logical Access & CC7 - System Operations",
        "organization": organization.name,
        "period": {"start": str(period_start), "end": str(period_end)},
        "entry_count": len(entries),
        "entries": entries,
        "summary": {
            "total_events": len(entries),
            "unique_actors": len({e["actor"] for e in entries}),
            "approval_events": sum(1 for e in entries if e["action"] in ("approve", "reject")),
        },
    }

    return ComplianceReport.objects.create(
        organization=organization,
        report_type=ComplianceReport.ReportType.SOC2_AUDIT,
        title=f"SOC 2 Audit Trail — {period_start} to {period_end}",
        generated_by=generated_by,
        period_start=period_start,
        period_end=period_end,
        payload=payload,
    )


def generate_approval_chain_report(organization, *, period_start, period_end, generated_by):
    approvals = ApprovalRequest.objects.filter(
        run__workflow__organization=organization,
        created_at__date__gte=period_start,
        created_at__date__lte=period_end,
    ).select_related("decided_by", "run")

    payload = {
        "framework": "Approval Chain Evidence",
        "organization": organization.name,
        "period": {"start": str(period_start), "end": str(period_end)},
        "chains": [
            {
                "approval_id": a.id,
                "title": a.title,
                "status": a.status,
                "approver_group": a.approver_group,
                "decided_by": a.decided_by.username if a.decided_by else None,
                "decided_at": a.decided_at.isoformat() if a.decided_at else None,
                "run_id": str(a.run_id),
                "note": a.decision_note,
            }
            for a in approvals
        ],
    }

    return ComplianceReport.objects.create(
        organization=organization,
        report_type=ComplianceReport.ReportType.APPROVAL_CHAIN,
        title=f"Approval Chain Report — {period_start} to {period_end}",
        generated_by=generated_by,
        period_start=period_start,
        period_end=period_end,
        payload=payload,
    )
