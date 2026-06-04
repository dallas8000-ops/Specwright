from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.views import CurrentUserMixin

from .models import Department, Membership, Organization
from .permissions import IsOrgMember
from .serializers import DepartmentSerializer, OrganizationSerializer


class OrganizationViewSet(CurrentUserMixin, viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    lookup_field = "slug"

    def get_queryset(self):
        return Organization.objects.filter(
            memberships__user=self.request.user,
            is_active=True,
        ).distinct()


class DepartmentViewSet(CurrentUserMixin, viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["organization", "department_type"]

    def get_queryset(self):
        return Department.objects.filter(
            organization__memberships__user=self.request.user,
            organization__is_active=True,
        ).distinct()
