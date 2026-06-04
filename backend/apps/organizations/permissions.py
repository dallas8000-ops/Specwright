from rest_framework.permissions import BasePermission

from .models import Membership


class IsOrgMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        org = getattr(obj, "organization", obj)
        return Membership.objects.filter(
            user=request.user, organization=org, organization__is_active=True
        ).exists()


class IsOrgAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        org = getattr(obj, "organization", obj)
        return Membership.objects.filter(
            user=request.user,
            organization=org,
            role__in=("admin", "owner"),
        ).exists()
