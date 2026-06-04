from django.contrib import admin

from .models import StepRun, WorkflowRun


class StepRunInline(admin.TabularInline):
    model = StepRun
    extra = 0
    readonly_fields = ("node_key", "status", "started_at", "finished_at")


@admin.register(WorkflowRun)
class WorkflowRunAdmin(admin.ModelAdmin):
    list_display = ("id", "workflow", "status", "trigger_source", "started_at")
    list_filter = ("status", "trigger_source")
    inlines = [StepRunInline]
