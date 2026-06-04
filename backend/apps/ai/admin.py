from django.contrib import admin

from .models import AIAssessment, AICopilotMessage


@admin.register(AIAssessment)
class AIAssessmentAdmin(admin.ModelAdmin):
    list_display = ("kind", "vertical", "case", "confidence", "model_name", "created_at")
    list_filter = ("kind", "vertical")


@admin.register(AICopilotMessage)
class AICopilotMessageAdmin(admin.ModelAdmin):
    list_display = ("case", "role", "created_at")
