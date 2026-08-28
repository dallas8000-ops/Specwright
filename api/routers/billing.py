from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import settings
from api.core.database import get_db
from api.models.tables import Project
from api.schemas import BillingStatusOut, CheckoutOut, PricingCatalog
from api.services import billing_service
from api.services.stripe_resilience import StripeOperationError

router = APIRouter(prefix="/billing", tags=["billing"])


def _effective_plan(projects: list[Project]) -> str:
    if any(p.plan == "enterprise" for p in projects):
        return "enterprise"
    if any(p.plan == "pro" for p in projects):
        return "pro"
    if any(p.plan == "starter" for p in projects):
        return "starter"
    return "starter"


@router.get("/status", response_model=BillingStatusOut)
async def billing_status(db: AsyncSession = Depends(get_db)):
    projects = (await db.execute(select(Project))).scalars().all()
    plan = _effective_plan(projects)
    info = billing_service.get_plan_status(plan)
    return BillingStatusOut(
        plan=info["plan"],
        is_pro=info["is_pro"],
        is_starter=info["is_starter"],
        features=info["features"],
        stripe_configured=billing_service.billing_configured(),
        catalog=PricingCatalog(**info["catalog"]),
    )


@router.post("/checkout", response_model=CheckoutOut)
async def create_checkout(
    tier: str = Query("pro", pattern="^(starter|pro)$"),
    annual: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    success = f"{settings.frontend_url}/billing?success=1&tier={tier}"
    cancel = f"{settings.frontend_url}/billing?canceled=1"
    try:
        result = await billing_service.create_checkout_session(
            success, cancel, tier=tier, annual=annual
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except StripeOperationError as e:
        raise HTTPException(
            503,
            {
                "message": e.failure.message,
                "category": e.failure.category,
                "retryable": e.failure.retryable,
                "request_id": e.failure.request_id,
            },
        ) from e

    if result.get("mode") == "mock":
        projects = (await db.execute(select(Project))).scalars().all()
        for p in projects:
            p.plan = tier
        await db.commit()

    return CheckoutOut(**result)


@router.post("/webhook/", include_in_schema=False)
@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature")
    try:
        result = await billing_service.handle_stripe_webhook(payload, sig)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    tier = result.get("plan", "pro")
    if tier in ("starter", "pro", "enterprise"):
        projects = (await db.execute(select(Project))).scalars().all()
        for p in projects:
            p.plan = tier
        await db.commit()

    return result


@router.post("/activate-mock/{project_id}")
async def activate_mock_pro(project_id: int, db: AsyncSession = Depends(get_db)):
    """Dev-only: upgrade a project to Pro without Stripe."""
    if not settings.billing_mock_mode:
        raise HTTPException(
            403,
            "Mock billing is disabled. Set SPECWRIGHT_BILLING_MOCK_MODE=true for local dev.",
        )
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project.plan = "pro"
    await db.commit()
    return {"ok": True, "plan": "pro", "project_id": project_id}


@router.post("/activate-mock")
async def activate_mock_pro_all(db: AsyncSession = Depends(get_db)):
    """Dev-only: upgrade all projects to Pro."""
    if not settings.billing_mock_mode:
        raise HTTPException(403, "Mock billing is disabled.")
    projects = (await db.execute(select(Project))).scalars().all()
    for p in projects:
        p.plan = "pro"
    await db.commit()
    return {"ok": True, "plan": "pro", "projects_updated": len(projects)}
