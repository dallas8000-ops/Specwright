import datetime as dt

import pytest
from django.contrib.auth import get_user_model

from apps.compliance.models import AccessReviewSchedule
from apps.organizations.models import Membership, Organization


@pytest.mark.django_db
def test_admin_route_is_reachable(client):
    response = client.get("/admin/")
    assert response.status_code in {200, 302}


@pytest.mark.django_db
def test_auth_users_create_route_registers_user(client):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "very-strong-pass",
        "first_name": "New",
        "last_name": "User",
    }
    response = client.post("/api/auth/users/", payload)

    assert response.status_code == 201
    User = get_user_model()
    assert User.objects.filter(username="newuser").exists()


@pytest.mark.django_db
def test_reports_schedules_requires_authentication(client):
    response = client.get("/api/reports/schedules/")
    assert response.status_code in {401, 403}


@pytest.mark.django_db
def test_reports_schedules_lists_active_membership_data(client):
    User = get_user_model()
    user = User.objects.create_user(
        username="memberuser",
        email="member@example.com",
        password="strong-pass-123",
    )
    org = Organization.objects.create(name="Acme", slug="acme")
    Membership.objects.create(user=user, organization=org, is_primary=True)
    AccessReviewSchedule.objects.create(
        organization=org,
        name="Quarterly Review",
        cadence_days=90,
        next_review_at=dt.date.today(),
        owner=user,
        is_active=True,
    )

    client.force_login(user)
    response = client.get("/api/reports/schedules/")

    assert response.status_code == 200
    body = response.json()
    results = body.get("results", body)
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["name"] == "Quarterly Review"