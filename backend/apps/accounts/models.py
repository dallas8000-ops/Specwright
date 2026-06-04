from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        ORG_ADMIN = "org_admin", "Organization Admin"
        DEPT_LEAD = "dept_lead", "Department Lead"
        BUILDER = "builder", "Workflow Builder"
        OPERATOR = "operator", "Operator"
        VIEWER = "viewer", "Viewer"

    class Persona(models.TextChoices):
        """Vertical persona — entire UI adapts to this, not just permissions."""
        HR_SPECIALIST = "hr_specialist", "HR Specialist"
        LEGAL_COUNSEL = "legal_counsel", "Legal Counsel"
        LOGISTICS_COORDINATOR = "logistics_coordinator", "Logistics Coordinator"
        COMPLIANCE_OFFICER = "compliance_officer", "Compliance Officer"
        OPS_ADMIN = "ops_admin", "Operations Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.OPERATOR)
    persona = models.CharField(
        max_length=32, choices=Persona.choices, default=Persona.OPS_ADMIN, blank=True
    )
    job_title = models.CharField(max_length=128, blank=True)
    phone = models.CharField(max_length=32, blank=True)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.get_full_name() or self.username
