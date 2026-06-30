"""Stripe checkout and plan management."""
from __future__ import annotations

from api.core.config import settings
from api.services.stripe_resilience import call_stripe

FEATURE_MATRIX = [
    {"name": "Unlimited codebase scans", "starter": True, "pro": True, "enterprise": True},
    {"name": "OpenAPI + markdown API docs", "starter": True, "pro": True, "enterprise": True},
    {"name": "Pytest scaffolds & ER diagrams", "starter": True, "pro": True, "enterprise": True},
    {"name": "Watch mode (auto re-scan)", "starter": True, "pro": True, "enterprise": True},
    {"name": "Export & CI-ready artifacts", "starter": True, "pro": True, "enterprise": True},
    {"name": "AI markdown polish", "starter": False, "pro": True, "enterprise": True},
    {
        "name": "Grounded AI (descriptions, migration, tests, chat)",
        "starter": False,
        "pro": True,
        "enterprise": True,
    },
    {"name": "GitHub PR comments & webhooks", "starter": False, "pro": True, "enterprise": True},
    {"name": "Priority support", "starter": False, "pro": True, "enterprise": True},
    {"name": "SSO / SAML", "starter": False, "pro": False, "enterprise": True},
    {"name": "Dedicated success manager", "starter": False, "pro": False, "enterprise": True},
    {"name": "Custom SLA & audit logs", "starter": False, "pro": False, "enterprise": True},
]


def billing_configured() -> bool:
    return bool(settings.stripe_secret_key and settings.stripe_price_id_pro)


def get_pricing_catalog() -> dict:
    return {
        "currency": "USD",
        "starter_price_usd": settings.starter_price_usd,
        "pro_price_usd": settings.pro_price_usd,
        "pro_interval": "month",
        "pro_trial_days": settings.pro_trial_days,
        "annual_discount_percent": settings.annual_discount_percent,
        "starter_annual_usd": int(settings.starter_price_usd * 12 * 0.8),
        "pro_annual_usd": int(settings.pro_price_usd * 12 * 0.8),
        "feature_matrix": FEATURE_MATRIX,
        "stripe_live": billing_configured(),
    }


def get_plan_status(plan: str) -> dict:
    catalog = get_pricing_catalog()
    is_pro = plan in ("pro", "enterprise")
    is_starter = plan == "starter"
    return {
        "plan": plan,
        "is_pro": is_pro,
        "is_starter": is_starter,
        "features": [r["name"] for r in FEATURE_MATRIX if r.get(plan, False)],
        "catalog": catalog,
    }


async def create_checkout_session(
    success_url: str,
    cancel_url: str,
    *,
    tier: str = "pro",
    annual: bool = False,
) -> dict:
    if tier not in ("starter", "pro"):
        raise ValueError("Checkout is available for Starter and Pro. Contact sales for Enterprise.")

    if not billing_configured():
        if settings.billing_mock_mode:
            return {"mode": "mock", "url": success_url, "tier": tier}
        raise ValueError(
            "Payments are temporarily unavailable. Email sales@specwright.dev for Enterprise."
        )

    import stripe

    price_id = (
        settings.stripe_price_id_pro
        if tier == "pro"
        else settings.stripe_price_id_starter or settings.stripe_price_id_pro
    )
    if not price_id:
        raise ValueError("Stripe price ID is not configured for this tier.")

    stripe.api_key = settings.stripe_secret_key
    stripe.api_version = settings.stripe_api_version
    session_kwargs: dict = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "allow_promotion_codes": True,
        "billing_address_collection": "auto",
        "metadata": {"tier": tier},
    }
    if tier == "pro" and settings.pro_trial_days > 0:
        session_kwargs["subscription_data"] = {
            "trial_period_days": settings.pro_trial_days,
        }
    session = await call_stripe(
        "checkout.session.create",
        stripe.checkout.Session.create,
        max_attempts=settings.stripe_retry_attempts,
        **session_kwargs,
    )
    return {"mode": "stripe", "url": session.url, "session_id": session.id, "tier": tier}


async def handle_stripe_webhook(payload: bytes, sig_header: str | None) -> dict:
    if not settings.stripe_webhook_secret:
        raise ValueError("SPECWRIGHT_STRIPE_WEBHOOK_SECRET is not set")

    import stripe

    stripe.api_key = settings.stripe_secret_key
    stripe.api_version = settings.stripe_api_version
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.SignatureVerificationError as e:
        raise ValueError("Invalid signature") from e
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        tier = (session.get("metadata") or {}).get("tier", "pro")
        return {
            "received": True,
            "plan": tier,
            "customer_email": session.get("customer_details", {}).get("email"),
        }
    return {"received": True, "type": event["type"]}
