from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.cases.models import Case
from apps.compliance.models import AccessReviewSchedule
from apps.integrations.models import Connector
from apps.intelligence.services import refresh_institutional_memory, scan_proactive_alerts
from apps.organizations.models import Department, Membership, Organization
from apps.workflows.models import WorkflowTemplate

User = get_user_model()

TEMPLATES = [
    {
        "name": "Employee Onboarding",
        "slug": "employee-onboarding",
        "category": "hr",
        "description": "Automate offer letter, IT provisioning, and HR checklist for new hires.",
        "definition": {
            "nodes": [
                {"key": "start", "type": "trigger", "label": "New Hire Submitted", "x": 0, "y": 0},
                {"key": "hr_review", "type": "approval", "label": "HR Review", "x": 200, "y": 0, "config": {"approver_group": "hr", "sla_hours": 24}},
                {"key": "it_ticket", "type": "integration", "label": "Create IT Ticket", "x": 400, "y": 0, "config": {"connector": "rest-generic"}},
                {"key": "notify", "type": "notification", "label": "Welcome Email", "x": 600, "y": 0},
            ],
            "edges": [
                {"source": "start", "target": "hr_review"},
                {"source": "hr_review", "target": "it_ticket"},
                {"source": "it_ticket", "target": "notify"},
            ],
        },
    },
    {
        "name": "Contract Review & Approval",
        "slug": "contract-review",
        "category": "legal",
        "description": "Route contracts through legal review with value-based escalation.",
        "definition": {
            "nodes": [
                {"key": "start", "type": "trigger", "label": "Contract Uploaded", "x": 0, "y": 0},
                {"key": "value_check", "type": "condition", "label": "High Value?", "x": 200, "y": 0, "config": {"expression": "legal_review_required", "true_branch": "yes", "false_branch": "no"}},
                {"key": "legal_approval", "type": "approval", "label": "Legal Sign-off", "x": 400, "y": -80, "config": {"approver_group": "legal", "sla_hours": 72}},
                {"key": "auto_approve", "type": "action", "label": "Standard Approval", "x": 400, "y": 80},
                {"key": "docusign", "type": "integration", "label": "Send for Signature", "x": 600, "y": 0, "config": {"connector": "docusign"}},
            ],
            "edges": [
                {"source": "start", "target": "value_check"},
                {"source": "value_check", "target": "legal_approval", "label": "yes"},
                {"source": "value_check", "target": "auto_approve", "label": "no"},
                {"source": "legal_approval", "target": "docusign"},
                {"source": "auto_approve", "target": "docusign"},
            ],
        },
    },
    {
        "name": "Shipment Exception Handler",
        "slug": "shipment-exception",
        "category": "logistics",
        "description": "Detect delayed shipments, notify carriers, and escalate to ops.",
        "definition": {
            "nodes": [
                {"key": "webhook", "type": "trigger", "label": "TMS Alert", "x": 0, "y": 0},
                {"key": "classify", "type": "condition", "label": "Delay > 24h?", "x": 200, "y": 0, "config": {"expression": "delay_hours > 24", "true_branch": "yes"}},
                {"key": "carrier_api", "type": "integration", "label": "Query Carrier", "x": 400, "y": 0},
                {"key": "ops_escalation", "type": "approval", "label": "Ops Escalation", "x": 600, "y": 0, "config": {"approver_group": "logistics_ops"}},
                {"key": "slack_alert", "type": "notification", "label": "Slack Alert", "x": 800, "y": 0, "config": {"title": "Shipment Delay"}},
            ],
            "edges": [
                {"source": "webhook", "target": "classify"},
                {"source": "classify", "target": "carrier_api", "label": "yes"},
                {"source": "carrier_api", "target": "ops_escalation"},
                {"source": "ops_escalation", "target": "slack_alert"},
            ],
        },
    },
]

SYSTEM_CONNECTORS = [
    ("rest-generic", "REST API", "rest", "Generic REST connector for internal tools"),
    ("email-smtp", "Email (SMTP)", "email", "Send transactional email"),
    ("slack", "Slack", "slack", "Post messages to Slack channels"),
    ("workday", "Workday", "workday", "HRIS — employees, org units"),
    ("docusign", "DocuSign", "docusign", "E-signature envelopes"),
    ("sap-erp", "SAP ERP", "sap", "Purchase orders, inventory"),
]


class Command(BaseCommand):
    help = "Seed demo organization, templates, connectors, and admin user"

    def handle(self, *args, **options):
        # Three separate product tenants — NOT one generic tri-dept board
        tenants = [
            ("acme-legal", "Acme Legal (CounselFlow AI)", "legal", "legal", "legal.sam", User.Persona.LEGAL_COUNSEL),
            ("acme-people", "Acme People Ops (PeopleOps AI)", "hr", "hr", "hr.jordan", User.Persona.HR_SPECIALIST),
            ("acme-freight", "Acme Freight (FreightPulse AI)", "logistics", "logistics", "logistics.alex", User.Persona.LOGISTICS_COORDINATOR),
        ]
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@acme.internal",
                "is_staff": True,
                "is_superuser": True,
                "role": User.Role.SUPER_ADMIN,
                "persona": User.Persona.OPS_ADMIN,
            },
        )
        if admin.password == "" or not admin.check_password("changeme-in-production"):
            admin.set_password("changeme-in-production")
            admin.save()

        for slug, name, vertical, dept_slug, demo_user, persona in tenants:
            org, _ = Organization.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "domain": f"{slug}.internal",
                    "settings": {"primary_vertical": vertical},
                },
            )
            org.settings["primary_vertical"] = vertical
            org.save(update_fields=["settings"])
            Department.objects.get_or_create(
                organization=org,
                slug=dept_slug,
                defaults={"name": dept_slug.title(), "department_type": dept_slug},
            )
            user, created = User.objects.get_or_create(
                username=demo_user,
                defaults={"email": f"{demo_user}@acme.internal", "role": User.Role.DEPT_LEAD, "persona": persona},
            )
            if created:
                user.set_password("changeme-in-production")
                user.save()
            Membership.objects.get_or_create(user=user, organization=org, defaults={"role": "owner", "is_primary": True})
            Membership.objects.get_or_create(user=admin, organization=org, defaults={"role": "admin", "is_primary": False})
            self._seed_vertical_cases(org, vertical, user)

        self.stdout.write(self.style.WARNING("Demo: legal.sam / hr.jordan / logistics.alex — changeme-in-production"))
        self.stdout.write(self.style.WARNING("Each login is a DIFFERENT product tenant (not a generic board)."))

        for slug, name, kind, desc in SYSTEM_CONNECTORS:
            Connector.objects.get_or_create(
                slug=slug,
                organization=None,
                defaults={"name": name, "kind": kind, "description": desc, "is_system": True},
            )

        for tpl in TEMPLATES:
            WorkflowTemplate.objects.update_or_create(
                slug=tpl["slug"],
                defaults={
                    "name": tpl["name"],
                    "category": tpl["category"],
                    "description": tpl["description"],
                    "definition": tpl["definition"],
                    "is_public": True,
                },
            )

        for slug, _, vertical, _, _, _ in tenants:
            org = Organization.objects.get(slug=slug)
            refresh_institutional_memory(org)
            scan_proactive_alerts(org)

        self.stdout.write(self.style.SUCCESS("Three single-vertical AI product tenants seeded."))

    def _seed_vertical_cases(self, org, vertical, opener):
        dept = Department.objects.get(organization=org)
        if vertical == "legal":
            Case.objects.get_or_create(
                organization=org,
                department=dept,
                case_type=Case.CaseType.CONTRACT_REVIEW,
                title="MSA — Vendor NovaCloud ($120k)",
                defaults={
                    "summary": "Non-standard indemnity; DPA addendum; needs counsel before sign.",
                    "subject_key": "contract:C-8891",
                    "subject_label": "NovaCloud MSA",
                    "stage": Case.Stage.INVESTIGATION,
                    "opened_by": opener,
                    "priority": "critical",
                },
            )
        elif vertical == "hr":
            Case.objects.get_or_create(
                organization=org,
                department=dept,
                case_type=Case.CaseType.NEW_HIRE,
                title="Onboard — Priya Sharma (Engineering)",
                defaults={
                    "summary": "Start Monday; background check clear; IT bundle pending.",
                    "subject_key": "employee:E2041",
                    "subject_label": "Priya Sharma",
                    "stage": Case.Stage.INVESTIGATION,
                    "opened_by": opener,
                    "priority": "high",
                },
            )
        else:
            Case.objects.get_or_create(
                organization=org,
                department=dept,
                case_type=Case.CaseType.SHIPMENT_EXCEPTION,
                title="SH-4421 — 36h delay at Memphis hub",
                defaults={
                    "summary": "Customer OTIF at risk; carrier scan stale.",
                    "subject_key": "shipment:SH-4421",
                    "subject_label": "SH-4421",
                    "stage": Case.Stage.RESOLUTION,
                    "opened_by": opener,
                    "priority": "critical",
                },
            )
