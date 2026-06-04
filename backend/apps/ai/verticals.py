"""
Single-vertical product configuration — each tenant runs ONE serious ops product, not a generic tri-dept board.
"""

from enum import StrEnum


class PrimaryVertical(StrEnum):
    HR = "hr"
    LEGAL = "legal"
    LOGISTICS = "logistics"


VERTICAL_PRODUCT = {
    PrimaryVertical.HR: {
        "product_name": "PeopleOps AI",
        "tagline": "AI-assisted hire, policy, and access operations",
        "case_types": ["new_hire", "policy_exception", "access_review"],
        "forbidden_case_types": ["contract_review", "shipment_exception"],
    },
    PrimaryVertical.LEGAL: {
        "product_name": "CounselFlow AI",
        "tagline": "AI-assisted contract review, risk scoring, and sign-off orchestration",
        "case_types": ["contract_review"],
        "forbidden_case_types": ["new_hire", "shipment_exception", "policy_exception"],
    },
    PrimaryVertical.LOGISTICS: {
        "product_name": "FreightPulse AI",
        "tagline": "AI-assisted shipment exceptions, SLA recovery, and carrier coordination",
        "case_types": ["shipment_exception"],
        "forbidden_case_types": ["new_hire", "contract_review", "policy_exception"],
    },
}


def get_vertical(org) -> PrimaryVertical:
    raw = (org.settings or {}).get("primary_vertical", PrimaryVertical.LEGAL)
    try:
        return PrimaryVertical(raw)
    except ValueError:
        return PrimaryVertical.LEGAL


def vertical_config(org) -> dict:
    v = get_vertical(org)
    return {"vertical": v, **VERTICAL_PRODUCT[v]}
