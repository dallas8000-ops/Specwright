import pytest
from django.contrib.auth import get_user_model

from apps.events.models import DomainEvent
from apps.organizations.models import Membership, Organization


@pytest.mark.django_db
def test_service_registry_requires_authentication(client):
    response = client.get("/api/services/")
    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_service_registry_returns_architecture_and_services(client):
    User = get_user_model()
    user = User.objects.create_user(
        username="events-api-user",
        email="events-api-user@example.com",
        password="pass12345",
    )
    client.force_login(user)

    response = client.get("/api/services/")

    assert response.status_code == 200
    body = response.json()
    assert body["architecture"] == "event-driven service-oriented"
    assert isinstance(body["services"], list)
    assert len(body["services"]) >= 5


@pytest.mark.django_db
def test_domain_event_list_is_scoped_to_user_memberships(client):
    User = get_user_model()
    user = User.objects.create_user(
        username="domain-events-user",
        email="domain-events-user@example.com",
        password="pass12345",
    )
    org_allowed = Organization.objects.create(name="Allowed Org", slug="allowed-org")
    org_other = Organization.objects.create(name="Other Org", slug="other-org")
    Membership.objects.create(user=user, organization=org_allowed, role="member")

    DomainEvent.objects.create(
        service="execution_service",
        event_type="run.started",
        organization_id=org_allowed.id,
        aggregate_type="workflow_run",
        aggregate_id="1",
        payload={"ok": True},
        correlation_id="corr-allowed",
    )
    DomainEvent.objects.create(
        service="execution_service",
        event_type="run.started",
        organization_id=org_other.id,
        aggregate_type="workflow_run",
        aggregate_id="2",
        payload={"ok": False},
        correlation_id="corr-other",
    )

    client.force_login(user)
    response = client.get("/api/domain-events/")

    assert response.status_code == 200
    body = response.json()
    results = body.get("results", body)
    assert len(results) == 1
    assert results[0]["organization_id"] == org_allowed.id
    assert results[0]["correlation_id"] == "corr-allowed"
