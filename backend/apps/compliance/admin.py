from django.contrib import admin

from .models import AccessReviewSchedule, ComplianceReport


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ("title", "report_type", "organization", "created_at")
    list_filter = ("report_type",)


@admin.register(AccessReviewSchedule)
class AccessReviewScheduleAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "next_review_at", "cadence_days")
