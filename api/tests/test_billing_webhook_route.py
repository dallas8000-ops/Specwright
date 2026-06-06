import httpx
import pytest

from api.main import app


@pytest.mark.anyio
async def test_billing_webhook_returns_plan_from_service(monkeypatch):
    async def fake_handle(payload: bytes, sig_header: str | None):
        return {
            "received": True,
            "plan": "pro",
            "customer_email": "billing@example.com",
        }

    monkeypatch.setattr(
        "api.routers.billing.billing_service.handle_stripe_webhook",
        fake_handle,
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/billing/webhook",
            content="{}",
            headers={"Stripe-Signature": "sig"},
        )

    assert response.status_code == 200
    assert response.json()["plan"] == "pro"


@pytest.mark.anyio
async def test_billing_webhook_returns_400_on_service_error(monkeypatch):
    async def fake_handle(payload: bytes, sig_header: str | None):
        raise ValueError("bad signature")

    monkeypatch.setattr(
        "api.routers.billing.billing_service.handle_stripe_webhook",
        fake_handle,
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/billing/webhook", content="{}")

    assert response.status_code == 400
    assert response.json()["detail"] == "bad signature"