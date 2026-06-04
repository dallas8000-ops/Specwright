from django.contrib import admin

from .models import MemoryInsight, ProactiveAlert


@admin.register(MemoryInsight)
class MemoryInsightAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "severity", "occurrence_count", "last_seen")
    list_filter = ("kind", "severity")


@admin.register(ProactiveAlert)
class ProactiveAlertAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "severity", "acknowledged", "escalated", "created_at")
    list_filter = ("kind", "acknowledged")
