from django.contrib import admin

from .models import ApprovalRequest


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "run", "status", "approver_group", "due_at", "created_at")
    list_filter = ("status",)
