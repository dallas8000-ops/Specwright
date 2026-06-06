from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import MeView, RegisterView
from apps.context.views import ScreenContextView
from apps.ai.views import AIAssessmentViewSet, AICaseActionsViewSet, nl_intake, product_config
from apps.events.views import DomainEventViewSet, service_registry
from apps.approvals.views import ApprovalRequestViewSet
from apps.audit.views import AuditLogViewSet
from apps.cases.views import CaseViewSet
from apps.compliance.views import AccessReviewScheduleViewSet, ComplianceReportViewSet
from apps.executions.views import WorkflowRunViewSet, trigger_webhook
from apps.integrations.views import ConnectorViewSet, CredentialViewSet, slack_interaction
from apps.intelligence.views import MemoryInsightViewSet, ProactiveAlertViewSet
from apps.notifications.views import NotificationViewSet
from apps.organizations.views import DepartmentViewSet, OrganizationViewSet
from apps.workflows.views import WorkflowTemplateViewSet, WorkflowViewSet

router = DefaultRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"workflows", WorkflowViewSet, basename="workflow")
router.register(r"workflow-templates", WorkflowTemplateViewSet, basename="workflow-template")
router.register(r"connectors", ConnectorViewSet, basename="connector")
router.register(r"credentials", CredentialViewSet, basename="credential")
router.register(r"runs", WorkflowRunViewSet, basename="run")
router.register(r"approvals", ApprovalRequestViewSet, basename="approval")
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"cases", CaseViewSet, basename="case")
router.register(r"insights", MemoryInsightViewSet, basename="insight")
router.register(r"alerts", ProactiveAlertViewSet, basename="alert")
router.register(r"compliance-reports", ComplianceReportViewSet, basename="compliance-report")
router.register(r"access-reviews", AccessReviewScheduleViewSet, basename="access-review")
router.register(r"domain-events", DomainEventViewSet, basename="domain-event")
router.register(r"ai-assessments", AIAssessmentViewSet, basename="ai-assessment")
router.register(r"ai/cases", AICaseActionsViewSet, basename="ai-case")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/users/", RegisterView.as_view(), name="auth-users"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/screen-context/<str:screen>/", ScreenContextView.as_view(), name="screen-context"),
    path("api/services/", service_registry, name="service-registry"),
    path("api/ai/product/", product_config, name="ai-product"),
    path("api/ai/intake/", nl_intake, name="ai-intake"),
    path("api/webhooks/<slug:workflow_slug>/", trigger_webhook, name="webhook-trigger"),
    path("api/integrations/slack/interaction/", slack_interaction, name="slack-interaction"),
    path(
        "api/reports/schedules/",
        AccessReviewScheduleViewSet.as_view({"get": "list"}),
        name="reports-schedules",
    ),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
