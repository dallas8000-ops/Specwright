from rest_framework import serializers

from .models import Department, Membership, Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "domain", "settings", "is_active", "created_at")
        read_only_fields = ("id", "created_at")


class DepartmentSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Department
        fields = (
            "id",
            "organization",
            "organization_name",
            "name",
            "slug",
            "department_type",
            "settings",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Membership
        fields = (
            "id",
            "user",
            "user_email",
            "organization",
            "department",
            "role",
            "is_primary",
            "joined_at",
        )
        read_only_fields = ("id", "joined_at")
