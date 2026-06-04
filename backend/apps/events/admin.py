from django.contrib import admin

from .models import DomainEvent


@admin.register(DomainEvent)
class DomainEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "service", "organization_id", "aggregate_id", "created_at")
    list_filter = ("service", "event_type")
