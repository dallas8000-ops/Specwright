import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from apps.audit.models import AuditLog
from apps.audit.services import log_action


@pytest.mark.django_db
def test_log_action_records_actor_org_and_metadata(monkeypatch):
    user = get_user_model().objects.create_user(
        username="audit-user",
        email="audit-user@example.com",
        password="pass12345",
    )

    request = type(
        "Request",
        (),
        {
            "user": user,
            "META": {
                "REMOTE_ADDR": "127.0.0.1",
                "HTTP_USER_AGENT": "pytest-agent",
            },
        },
    )()
    monkeypatch.setattr("apps.audit.services.get_current_request", lambda: request)

    payload = {"organization_id": 7, "event": "created"}
    log_action(
        action="create",
        resource_type="workflow",
        resource_id=123,
        metadata=payload,
    )

    record = AuditLog.objects.get()
    assert record.actor_id == user.id
    assert record.organization_id == 7
    assert record.resource_id == "123"
    assert record.ip_address == "127.0.0.1"
    assert record.user_agent == "pytest-agent"
    assert record.metadata == {"event": "created"}


@pytest.mark.django_db
def test_log_action_handles_anonymous_request(monkeypatch):
    request = type(
        "Request",
        (),
        {
            "user": AnonymousUser(),
            "META": {},
        },
    )()
    monkeypatch.setattr("apps.audit.services.get_current_request", lambda: request)

    log_action(action="export", resource_type="report", resource_id="abc")

    record = AuditLog.objects.get()
    assert record.actor is None
    assert record.organization_id is None
    assert record.ip_address is None
    assert record.user_agent == ""
    assert record.metadata == {}
