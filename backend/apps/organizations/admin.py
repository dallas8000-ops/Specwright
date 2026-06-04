from django.contrib import admin

from .models import Department, Membership, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "department_type")
    list_filter = ("department_type",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "department", "role", "is_primary")
    list_filter = ("role",)
