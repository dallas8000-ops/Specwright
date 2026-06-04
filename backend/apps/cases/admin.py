from django.contrib import admin

from .models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("title", "case_type", "stage", "department", "priority", "updated_at")
    list_filter = ("case_type", "stage", "priority")
