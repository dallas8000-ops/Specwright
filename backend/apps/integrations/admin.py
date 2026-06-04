from django.contrib import admin

from .models import Connector, Credential, IntegrationLog


@admin.register(Connector)
class ConnectorAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "organization", "is_system", "is_active")
    list_filter = ("kind", "is_system")


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ("name", "connector", "organization", "expires_at")


@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = ("connector", "success", "status_code", "duration_ms", "created_at")
    list_filter = ("success",)
