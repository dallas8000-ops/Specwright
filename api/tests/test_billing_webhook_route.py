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
async def test_trailing_slash_webhook_is_handled_without_redirect(monkeypatch):
    async def fake_handle(payload: bytes, sig_header: str | None):
        return {"received": True, "type": "ping"}

    monkeypatch.setattr(
        "api.routers.billing.billing_service.handle_stripe_webhook",
        fake_handle,
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/billing/webhook/",
            content="{}",
            headers={"Stripe-Signature": "sig"},
            follow_redirects=False,
        )

    assert response.status_code == 200
    assert response.history == []


@pytest.mark.anyio
async def test_billing_webhook_returns_400_on_stripe_signature_error(monkeypatch):
    import stripe

    def fake_construct_event(*_args, **_kwargs):
        raise stripe.SignatureVerificationError("bad sig", sig_header="sig")

    monkeypatch.setattr(stripe.Webhook, "construct_event", fake_construct_event)
    monkeypatch.setattr(
        "api.services.billing_service.settings.stripe_webhook_secret",
        "whsec_test",
    )
    monkeypatch.setattr(
        "api.services.billing_service.settings.stripe_secret_key",
        "sk_test_fake",
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/billing/webhook",
            content="{}",
            headers={"Stripe-Signature": "sig"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"


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