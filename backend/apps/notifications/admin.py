from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "channel", "priority", "is_read", "created_at")
    list_filter = ("channel", "priority", "is_read")
