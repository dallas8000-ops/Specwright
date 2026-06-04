"""
Turn operational data into narrative context — what / who / why / next.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone


def meaning_dict(
    *,
    what_happened: str,
    who: str,
    why_it_matters: str,
    what_next: str,
    actions: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "what_happened": what_happened,
        "who": who,
        "why_it_matters": why_it_matters,
        "what_next": what_next,
        "actions": actions or [],
    }


def case_meaning(case, *, viewer_username: str) -> dict:
    opened = case.opened_by.get_full_name() or case.opened_by.username if case.opened_by else "System"
    assigned = (
        case.assigned_to.get_full_name() or case.assigned_to.username
        if case.assigned_to
        else "Unassigned"
    )
    age_days = (timezone.now() - case.updated_at).days

    what = (
        f"{case.get_case_type_display()} «{case.title}» is in {case.get_stage_display()}"
        f"{f' regarding {case.subject_label}' if case.subject_label else ''}."
    )
    if age_days >= 3 and case.stage not in (case.Stage.POST_REVIEW,):
        what += f" No movement for {age_days} days."

    who = f"Opened by {opened}. Currently owned by {assigned} ({case.department.name})."

    why_map = {
        case.CaseType.NEW_HIRE: "Delayed onboarding blocks start date, IT access, and payroll cutover.",
        case.CaseType.CONTRACT_REVIEW: "Unsigned or unreviewed contracts create liability and revenue risk.",
        case.CaseType.SHIPMENT_EXCEPTION: "SLA misses trigger customer penalties and carrier chargebacks.",
        case.CaseType.POLICY_EXCEPTION: "Exceptions without audit trail fail internal control reviews.",
        case.CaseType.ACCESS_REVIEW: "Dormant or excessive access is a SOC 2 and HIPAA finding waiting to happen.",
    }
    why = why_map.get(case.case_type, "Unresolved cases compound cost and compliance exposure.")

    if case.priority == "critical":
        why = f"CRITICAL: {why}"

    next_stage = None
    try:
        idx = case.STAGE_ORDER.index(case.stage)
        if idx < len(case.STAGE_ORDER) - 1:
            next_stage = case.STAGE_ORDER[idx + 1]
    except ValueError:
        pass

    if next_stage:
        stage_label = Case.Stage(next_stage).label
        nxt = f"Advance to {stage_label} — {stage_action_hint(next_stage)}"
        actions = [{"label": f"Advance to {stage_label}", "action": "advance"}]
    else:
        nxt = "Close the post-review loop and capture lessons learned."
        actions = [{"label": "View audit trail", "href": "/audit"}]

    if case.assigned_to_id is None and viewer_username:
        nxt = f"Assign an owner first, then {nxt.lower()}"

    return meaning_dict(what_happened=what, who=who, why_it_matters=why, what_next=nxt, actions=actions)


def stage_action_hint(stage: str) -> str:
    hints = {
        "intake": "confirm facts and priority",
        "investigation": "gather evidence and required sign-offs",
        "resolution": "execute the fix (ticket, signature, carrier)",
        "post_review": "document what changed so it does not repeat",
    }
    return hints.get(stage, "follow the playbook")


def approval_meaning(approval) -> dict:
    what = f"Sign-off «{approval.title}» is {approval.get_status_display().lower()} for playbook {approval.run.workflow.name}."
    if approval.status == approval.Status.PENDING and approval.due_at:
        if approval.due_at < timezone.now():
            what += " It is past due."
        else:
            hours = (approval.due_at - timezone.now()).total_seconds() / 3600
            if hours < 24:
                what += f" Due in {int(hours)} hours."

    who = f"Routed to group «{approval.approver_group or 'general'}»."
    if approval.assigned_to:
        who += f" Assigned to {approval.assigned_to.get_full_name() or approval.assigned_to.username}."
    if approval.decided_by:
        who += f" Decided by {approval.decided_by.username} at {approval.decided_at}."

    why = "Playbooks cannot proceed until this control point is satisfied — downstream integrations are blocked."
    if approval.approver_group == "legal":
        why = "Legal must clear liability on contract value and terms before e-signature or payment."
    elif approval.approver_group == "hr":
        why = "HR clearance protects payroll, benefits eligibility, and policy consistency."

    if approval.status == approval.Status.PENDING:
        nxt = "Approve to resume automation, or reject with a note to stop the run."
        actions = [
            {"label": "Approve & resume", "action": "approve"},
            {"label": "Reject with reason", "action": "reject"},
        ]
    else:
        nxt = "No action required — archived for audit."
        actions = [{"label": "View run", "href": f"/runs"}]

    return meaning_dict(what_happened=what, who=who, why_it_matters=why, what_next=nxt, actions=actions)


def run_meaning(run) -> dict:
    what = f"Playbook «{run.workflow.name}» run {str(run.id)[:8]} is {run.get_status_display().lower()}."
    if run.error_message:
        what += f" Error: {run.error_message[:120]}"
    if run.sla_deadline and run.status in (run.Status.RUNNING, run.Status.WAITING):
        if run.sla_deadline < timezone.now():
            what += " SLA already breached."
        elif run.sla_deadline < timezone.now() + timedelta(hours=4):
            what += " SLA at risk within 4 hours."

    who = "Triggered via webhook"
    if run.triggered_by:
        who = f"Started by {run.triggered_by.get_full_name() or run.triggered_by.username} ({run.trigger_source})"

    why = "Failed or stuck runs leave integrations half-done — tickets, signatures, and carrier updates may not fire."
    if run.status == run.Status.WAITING:
        why = "Run is paused on a human gate; SLA clock may still be running."

    status_next = {
        run.Status.FAILED: "Open the case, fix input data, and re-run the playbook from the failed step.",
        run.Status.WAITING: "Clear the pending sign-off in your inbox to resume.",
        run.Status.COMPLETED: "Confirm downstream systems received updates; no action unless audit sampling.",
        run.Status.RUNNING: "Monitor — no action unless SLA warning fires.",
    }
    nxt = status_next.get(run.status, "Review run steps in the execution log.")
    actions = []
    if run.status == run.Status.WAITING:
        actions.append({"label": "Go to sign-offs", "href": "/approvals"})
    if run.status == run.Status.FAILED:
        actions.append({"label": "Open related case", "href": "/cases"})

    return meaning_dict(what_happened=what, who=who, why_it_matters=why, what_next=nxt, actions=actions)


def alert_meaning(alert) -> dict:
    what = alert.title + (f" — {alert.message}" if alert.message else "")
    who = f"Surfaced for {alert.recipient.username}" if alert.recipient else "Surfaced for ops team"
    if alert.escalated:
        who += " (escalated to Slack)"
    if alert.acknowledged:
        who += " — acknowledged"

    why_map = {
        alert.AlertKind.SLA_BREACH: "Missing SLA drives customer penalties and internal escalations.",
        alert.AlertKind.APPROVAL_OVERDUE: "Overdue sign-offs block hires, contracts, and shipments.",
        alert.AlertKind.CASE_STUCK: "Stuck cases hide root cause — risk repeats on the next incident.",
        alert.AlertKind.ACCESS_REVIEW_DUE: "Missed access reviews are audit findings.",
    }
    why = why_map.get(alert.kind, "Early warning prevents overnight surprises.")

    if alert.acknowledged:
        nxt = "Tracked — escalate only if situation worsens."
        actions = []
    else:
        nxt = "Acknowledge to confirm you saw it, or escalate to pull leadership into Slack."
        actions = [
            {"label": "Acknowledge", "action": "acknowledge"},
            {"label": "Escalate", "action": "escalate"},
        ]

    return meaning_dict(what_happened=what, who=who, why_it_matters=why, what_next=nxt, actions=actions)


def insight_meaning(insight) -> dict:
    what = insight.title
    who = f"Pattern detected across your org ({insight.occurrence_count}× recently)"
    if insight.subject_key:
        who += f" on {insight.subject_key}"

    why = insight.detail
    nxt = "Review linked cases or playbooks and schedule a post-review if this keeps recurring."
    actions = [{"label": "View cases", "href": "/cases"}]
    if insight.kind == insight.InsightKind.STALE_ACCESS:
        actions = [{"label": "Open compliance", "href": "/compliance"}]

    return meaning_dict(what_happened=what, who=who, why_it_matters=why, what_next=nxt, actions=actions)


def screen_context(screen: str, user, organization) -> dict:
    """Page-level narrative for the four context questions."""
    from apps.approvals.models import ApprovalRequest
    from apps.cases.models import Case
    from apps.executions.models import WorkflowRun
    from apps.intelligence.models import MemoryInsight, ProactiveAlert

    persona = user.persona or "ops_admin"
    now = timezone.now()

    builders = {
        "dashboard": _dashboard_screen,
        "cases": _cases_screen,
        "approvals": _approvals_screen,
        "runs": _runs_screen,
        "memory": _memory_screen,
        "compliance": _compliance_screen,
        "audit": _audit_screen,
        "templates": _templates_screen,
        "integrations": _integrations_screen,
        "workflows": _workflows_screen,
    }
    builder = builders.get(screen, _dashboard_screen)
    return builder(user, organization, persona, now, Case, ApprovalRequest, WorkflowRun, ProactiveAlert, MemoryInsight)


def _dashboard_screen(user, org, persona, now, Case, Approval, Run, Alert, Insight):
    pending = Approval.objects.filter(
        run__workflow__organization=org, status=Approval.Status.PENDING
    ).count()
    open_cases = Case.objects.filter(organization=org).exclude(stage=Case.Stage.POST_REVIEW).count()
    alerts = Alert.objects.filter(organization=org, acknowledged=False).count()
    failed = Run.objects.filter(
        workflow__organization=org,
        status=Run.Status.FAILED,
        started_at__gte=now - timedelta(days=7),
    ).count()

    what = f"Right now: {open_cases} open case(s), {pending} sign-off(s) waiting, {alerts} unacknowledged heads-up(s)."
    if failed:
        what += f" {failed} playbook failure(s) in the last 7 days."

    who = f"You are signed in as {user.get_full_name() or user.username} ({persona.replace('_', ' ')})."

    why_persona = {
        "hr_specialist": "Hiring and policy delays directly impact start dates and employee experience.",
        "legal_counsel": "Each pending contract is potential uncapped liability until counsel clears it.",
        "logistics_coordinator": "Shipment drift hits OTIF scorecards and customer renewals.",
        "compliance_officer": "Evidence gaps become audit findings — proactive beats reactive.",
        "ops_admin": "Cross-department friction shows up here before executives see it in QBRs.",
    }
    why = why_persona.get(persona, "Operational drag compounds when signals are ignored.")

    if pending:
        nxt = "Clear the oldest sign-off first — playbooks are blocked behind it."
    elif alerts:
        nxt = "Acknowledge the top heads-up, then open the linked case or run."
    elif open_cases:
        nxt = "Advance the highest-priority case one stage — do not let it sit in Investigation."
    else:
        nxt = "Open a new case from Quick Start — you're caught up on gates."

    actions = [
        {"label": "Sign-offs", "href": "/approvals"},
        {"label": "Cases", "href": "/cases"},
        {"label": "Heads-ups", "href": "/memory"},
    ]
    return meaning_dict(what_happened=what, who=who, why_it_matters=why, what_next=nxt, actions=actions)


def _cases_screen(user, org, persona, now, Case, *args):
    stuck = Case.objects.filter(
        organization=org,
        updated_at__lt=now - timedelta(days=3),
        stage__in=[Case.Stage.INVESTIGATION, Case.Stage.RESOLUTION],
    ).count()
    what = f"{Case.objects.filter(organization=org).count()} case(s) on the board."
    if stuck:
        what += f" {stuck} have not moved in 3+ days."
    who = f"{user.username} is viewing the {org.name} case queue."
    why = "Cases are the system of record — playbooks and sign-offs orbit around them."
    nxt = "Pick the critical or oldest case and advance it one stage today."
    return meaning_dict(
        what_happened=what,
        who=who,
        why_it_matters=why,
        what_next=nxt,
        actions=[{"label": "Quick-open case", "action": "quick_open"}],
    )


def _approvals_screen(user, org, persona, now, Case, Approval, *args):
    overdue = Approval.objects.filter(
        run__workflow__organization=org,
        status=Approval.Status.PENDING,
        due_at__lt=now,
    ).count()
    pending = Approval.objects.filter(
        run__workflow__organization=org, status=Approval.Status.PENDING
    ).count()
    what = f"{pending} sign-off(s) in queue."
    if overdue:
        what += f" {overdue} past due — playbooks are frozen."
    who = f"Decisions here are attributed to {user.username} in the audit trail."
    why = "This is your control layer — integrations will not fire until you approve."
    nxt = "Decide the overdue item first; add a rejection note if you need more information."
    return meaning_dict(
        what_happened=what,
        who=who,
        why_it_matters=why,
        what_next=nxt,
        actions=[{"label": "Oldest pending", "href": "/approvals"}],
    )


def _runs_screen(user, org, persona, now, Case, Approval, Run, *args):
    waiting = Run.objects.filter(workflow__organization=org, status=Run.Status.WAITING).count()
    failed = Run.objects.filter(workflow__organization=org, status=Run.Status.FAILED).count()
    what = f"Execution log: {waiting} run(s) waiting on people, {failed} failed."
    who = "Each run records who triggered it and which playbook version executed."
    why = "Runs are the receipt — proves what automation did when auditors ask."
    nxt = "Investigate failed runs first; waiting runs usually need a sign-off cleared."
    return meaning_dict(
        what_happened=what,
        who=who,
        why_it_matters=why,
        what_next=nxt,
        actions=[{"label": "Sign-offs", "href": "/approvals"}],
    )


def _memory_screen(user, org, persona, now, Case, Approval, Run, Alert, Insight):
    a = Alert.objects.filter(organization=org, acknowledged=False).count()
    i = Insight.objects.filter(organization=org).count()
    what = f"{a} active heads-up(s), {i} remembered pattern(s)."
    who = "Generated by hourly scans + your environment history — not manual reports."
    why = "Institutional memory turns repeat fires into fix-once work instead of firefighting weekly."
    nxt = "Run a fresh scan if data feels stale, then acknowledge or escalate each heads-up."
    return meaning_dict(
        what_happened=what,
        who=who,
        why_it_matters=why,
        what_next=nxt,
        actions=[{"label": "Run scan", "action": "refresh_scan"}],
    )


def _compliance_screen(user, org, persona, now, *args):
    from apps.compliance.models import AccessReviewSchedule

    due = AccessReviewSchedule.objects.filter(
        organization=org, is_active=True, next_review_at__lte=now.date() + timedelta(days=30)
    ).count()
    what = f"Compliance console for {org.name}."
    if due:
        what += f" {due} access review(s) due within 30 days."
    who = f"Reports generated by {user.username} are stamped in the audit log."
    why = "Regulators ask for evidence, not screenshots — exportable trails shorten audit weeks."
    nxt = "Generate a SOC 2 trail for the last 30 days before your next review meeting."
    return meaning_dict(
        what_happened=what,
        who=who,
        why_it_matters=why,
        what_next=nxt,
        actions=[{"label": "Generate SOC 2 report", "action": "generate_soc2"}],
    )


def _audit_screen(user, org, persona, now, *args):
    from apps.audit.models import AuditLog

    recent = AuditLog.objects.filter(created_at__gte=now - timedelta(days=1)).count()
    what = f"{recent} auditable event(s) in the last 24 hours (always recording)."
    who = "Every row shows actor, action, and resource — tamper-evident operational history."
    why = "When Legal or Compliance asks «who approved this?», this is the answer."
    nxt = "Filter to approve/reject actions when investigating a specific contract or hire."
    return meaning_dict(
        what_happened=what,
        who=who,
        why_it_matters=why,
        what_next=nxt,
        actions=[{"label": "Compliance export", "href": "/compliance"}],
    )


def _templates_screen(user, org, persona, now, *args):
    what = "Curated playbooks for hire, contract, and shipment workflows — not blank canvases."
    who = "Maintained by ops admin; Legal/HR/L Logistics own the underlying policy."
    why = "Starting from proven paths beats rebuilding integrations for every new process."
    nxt = "Clone the template closest to your process, publish, then bind it to case intake."
    return meaning_dict(
        what_happened=what,
        who=who,
        why_it_matters=why,
        what_next=nxt,
        actions=[{"label": "Cases", "href": "/cases"}],
    )


def _integrations_screen(user, org, persona, now, *args):
    what = "System connectors available for playbooks — credentials stored encrypted."
    who = f"Credential changes are attributed to admins; runs log integration attempts."
    why = "Shallow integrations fail silently — ours log success, latency, and payload shape."
    nxt = "Verify Slack webhook for actionable heads-ups before the next SLA incident."
    return meaning_dict(
        what_happened=what,
        who=who,
        why_it_matters=why,
        what_next=nxt,
        actions=[{"label": "Memory & alerts", "href": "/memory"}],
    )


def _workflows_screen(user, org, persona, now, *args):
    from apps.workflows.models import Workflow

    active = Workflow.objects.filter(organization=org, status=Workflow.Status.ACTIVE).count()
    draft = Workflow.objects.filter(organization=org, status=Workflow.Status.DRAFT).count()
    what = f"{active} live playbook(s), {draft} draft(s)."
    who = "Builders publish versions; operators execute — permissions separate the roles."
    why = "Unpublished drafts do not protect anyone — only active playbooks run in production."
    nxt = "Publish or pause drafts before go-live; tie each playbook to a case type."
    return meaning_dict(
        what_happened=what,
        who=who,
        why_it_matters=why,
        what_next=nxt,
        actions=[{"label": "Playbook library", "href": "/templates"}],
    )
