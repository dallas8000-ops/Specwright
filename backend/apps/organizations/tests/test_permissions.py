import pytest
from django.contrib.auth import get_user_model

from apps.organizations.models import Membership, Organization
from apps.organizations.permissions import IsOrgAdmin, IsOrgMember


class _OrgBoundObject:
    def __init__(self, organization):
        self.organization = organization


@pytest.mark.django_db
def test_is_org_member_allows_active_membership():
    user = get_user_model().objects.create_user(
        username="member-active",
        email="member-active@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Active Org", slug="active-org", is_active=True)
    Membership.objects.create(user=user, organization=org, role="member")

    permission = IsOrgMember()
    request = type("Request", (), {"user": user})()

    assert permission.has_object_permission(request, None, _OrgBoundObject(org)) is True


@pytest.mark.django_db
def test_is_org_member_denies_inactive_org():
    user = get_user_model().objects.create_user(
        username="member-inactive",
        email="member-inactive@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Inactive Org", slug="inactive-org", is_active=False)
    Membership.objects.create(user=user, organization=org, role="member")

    permission = IsOrgMember()
    request = type("Request", (), {"user": user})()

    assert permission.has_object_permission(request, None, org) is False


@pytest.mark.django_db
def test_is_org_admin_allows_admin_and_denies_member():
    User = get_user_model()
    admin_user = User.objects.create_user(
        username="org-admin",
        email="org-admin@example.com",
        password="pass12345",
    )
    member_user = User.objects.create_user(
        username="org-member",
        email="org-member@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Role Org", slug="role-org", is_active=True)
    Membership.objects.create(user=admin_user, organization=org, role="admin")
    Membership.objects.create(user=member_user, organization=org, role="member")

    permission = IsOrgAdmin()
    admin_request = type("Request", (), {"user": admin_user})()
    member_request = type("Request", (), {"user": member_user})()

    assert permission.has_object_permission(admin_request, None, org) is True
    assert permission.has_object_permission(member_request, None, org) is False


@pytest.mark.django_db
def test_is_org_admin_allows_owner_role_with_org_bound_object():
    user = get_user_model().objects.create_user(
        username="org-owner",
        email="org-owner@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Owner Org", slug="owner-org", is_active=True)
    Membership.objects.create(user=user, organization=org, role="owner")

    permission = IsOrgAdmin()
    request = type("Request", (), {"user": user})()

    assert permission.has_object_permission(request, None, _OrgBoundObject(org)) is True
