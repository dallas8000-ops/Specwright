from django.contrib import admin

from .models import Workflow, WorkflowEdge, WorkflowNode, WorkflowTemplate, WorkflowVersion


class WorkflowNodeInline(admin.TabularInline):
    model = WorkflowNode
    extra = 0


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "status", "trigger_type", "version")
    list_filter = ("status", "trigger_type")
    inlines = [WorkflowNodeInline]


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug", "is_public")
    list_filter = ("category",)


@admin.register(WorkflowVersion)
class WorkflowVersionAdmin(admin.ModelAdmin):
    list_display = ("workflow", "version_number", "published_at")
