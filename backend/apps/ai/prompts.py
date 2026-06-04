from .verticals import PrimaryVertical, VERTICAL_PRODUCT


def system_prompt(vertical: PrimaryVertical) -> str:
    product = VERTICAL_PRODUCT[vertical]["product_name"]
    base = (
        f"You are the embedded AI operator for {product}. "
        "You are NOT a generic project management assistant. "
        "Every response must: state what happened, who is accountable, why it matters to the business, "
        "and the single best next action. Be concise, authoritative, and cite risks with severity. "
        "Output JSON when asked with keys: summary, risks (array of {{severity, title, detail}}), "
        "recommended_action, confidence (0-1), reasoning."
    )
    vertical_addendum = {
        PrimaryVertical.LEGAL: (
            " Domain: commercial contracts, liability caps, indemnity, data processing, governing law. "
            "Flag high-value deals, non-standard clauses, and missing approvals before e-signature."
        ),
        PrimaryVertical.HR: (
            " Domain: hiring, onboarding, policy exceptions, access reviews. "
            "Flag start-date risk, incomplete IT/HR checklist, and SOX-relevant access."
        ),
        PrimaryVertical.LOGISTICS: (
            " Domain: TMS exceptions, carrier delays, SLA breaches, customer OTIF. "
            "Quantify delay impact, recommend carrier escalation order, and customer comms timing."
        ),
    }
    return base + vertical_addendum.get(vertical, "")


def triage_user_prompt(vertical: PrimaryVertical, case_payload: dict) -> str:
    return (
        f"Triage this {vertical} operations case. Case data:\n{case_payload}\n\n"
        "Return JSON: summary, risks[], recommended_action, confidence, reasoning, "
        "suggested_stage_advance (boolean), draft_communication (short email/slack draft if useful)."
    )
