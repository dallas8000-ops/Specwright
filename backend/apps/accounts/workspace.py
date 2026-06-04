"""Workspace driven by org vertical product — one serious product per tenant."""

from apps.ai.verticals import vertical_config

# Persona tweaks within the same vertical product
PERSONA_NAV = {
    "hr_specialist": ["home", "cases", "approvals", "memory"],
    "legal_counsel": ["home", "cases", "approvals", "compliance", "audit"],
    "logistics_coordinator": ["home", "cases", "runs", "approvals", "memory"],
    "compliance_officer": ["home", "cases", "compliance", "audit", "memory"],
    "ops_admin": ["home", "cases", "runs", "approvals", "memory"],
}

PERSONA_PRIMARY_ACTION = {
    "hr": {"label": "Describe hire situation (AI intake)", "case_type": "new_hire", "use_ai_intake": True},
    "legal": {"label": "Describe contract situation (AI intake)", "case_type": "contract_review", "use_ai_intake": True},
    "logistics": {
        "label": "Describe shipment problem (AI intake)",
        "case_type": "shipment_exception",
        "use_ai_intake": True,
    },
}


def get_workspace_for_user(user):
    membership = user.memberships.filter(is_primary=True).select_related("department", "organization").first()
    if not membership:
        membership = user.memberships.select_related("department", "organization").first()

    if not membership:
        return {"persona": user.persona, "experience": {}, "organization": None}

    org = membership.organization
    vcfg = vertical_config(org)
    vertical = vcfg["vertical"]
    persona = user.persona or "ops_admin"

    experience = {
        "app_title": vcfg["product_name"],
        "tagline": vcfg["tagline"],
        "vertical": vertical,
        "greeting": _vertical_greeting(vertical),
        "primary_action": PERSONA_PRIMARY_ACTION.get(
            vertical,
            {"label": "AI case intake", "case_type": vcfg["case_types"][0], "use_ai_intake": True},
        ),
        "nav": PERSONA_NAV.get(persona, PERSONA_NAV["ops_admin"]),
        "stat_labels": _vertical_stats(vertical),
        "enabled_case_types": vcfg["case_types"],
    }

    return {
        "persona": persona,
        "experience": experience,
        "organization": org.name,
        "department": membership.department.name if membership.department else None,
        "department_type": vertical,
    }


def _vertical_greeting(vertical: str) -> str:
    return {
        "legal": "Counsel AI is watching open matters — triage contracts before they slip.",
        "hr": "PeopleOps AI is watching open matters — don't let hires stall pre-start.",
        "logistics": "FreightPulse AI is watching exceptions — recover SLA before the customer calls.",
    }.get(vertical, "AI-assisted operations.")


def _vertical_stats(vertical: str) -> dict:
    return {
        "legal": {
            "cases": "Active matters",
            "approvals": "Counsel sign-offs",
            "alerts": "Deal risk flags",
        },
        "hr": {
            "cases": "Open people ops matters",
            "approvals": "HR clearances",
            "alerts": "Onboarding risk",
        },
        "logistics": {
            "cases": "Open exceptions",
            "approvals": "Ops escalations",
            "alerts": "SLA breach warnings",
        },
    }.get(vertical, {"cases": "Cases", "approvals": "Sign-offs", "alerts": "Alerts"})
