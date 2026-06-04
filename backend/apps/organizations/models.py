from django.conf import settings
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    domain = models.CharField(max_length=255, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    class DepartmentType(models.TextChoices):
        HR = "hr", "Human Resources"
        LEGAL = "legal", "Legal"
        LOGISTICS = "logistics", "Logistics"
        FINANCE = "finance", "Finance"
        IT = "it", "IT"
        OPERATIONS = "operations", "Operations"
        CUSTOM = "custom", "Custom"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="departments"
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    department_type = models.CharField(
        max_length=32, choices=DepartmentType.choices, default=DepartmentType.CUSTOM
    )
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("organization", "slug")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.organization.name} / {self.name}"


class Membership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships",
    )
    role = models.CharField(max_length=64, default="member")
    is_primary = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "organization")]

    def __str__(self):
        return f"{self.user} @ {self.organization}"
