"""Regression tests for GitHub webhook signature verification (fail-closed)."""
import hashlib
import hmac

from api.services import github_service


def _sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_rejects_when_secret_not_configured(monkeypatch):
    monkeypatch.setattr(github_service.settings, "github_webhook_secret", "")
    assert github_service.verify_webhook_signature(b"{}", None) is False
    assert github_service.verify_webhook_signature(b"{}", "sha256=anything") is False


def test_accepts_valid_signature(monkeypatch):
    monkeypatch.setattr(github_service.settings, "github_webhook_secret", "s3cret")
    body = b'{"action": "opened"}'
    assert github_service.verify_webhook_signature(body, _sign("s3cret", body)) is True


def test_rejects_bad_or_missing_signature(monkeypatch):
    monkeypatch.setattr(github_service.settings, "github_webhook_secret", "s3cret")
    body = b'{"action": "opened"}'
    assert github_service.verify_webhook_signature(body, None) is False
    assert github_service.verify_webhook_signature(body, "sha1=deadbeef") is False
    assert github_service.verify_webhook_signature(body, _sign("wrong", body)) is False


def test_webhook_route_returns_401_without_secret(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app

    monkeypatch.setattr(github_service.settings, "github_webhook_secret", "")
    response = TestClient(app).post("/api/v1/github/webhook", json={"action": "opened"})
    assert response.status_code == 401
