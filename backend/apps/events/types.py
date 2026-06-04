"""Domain event contracts between bounded contexts (service-oriented)."""

from enum import StrEnum


class Service(StrEnum):
    CASE = "case_service"
    APPROVAL = "approval_service"
    EXECUTION = "execution_service"
    INTELLIGENCE = "intelligence_service"
    NOTIFICATION = "notification_service"
    INTEGRATION = "integration_service"
    WORKFLOW = "workflow_service"
    AI = "ai_service"


class EventType(StrEnum):
    CASE_OPENED = "case.opened"
    CASE_STAGE_ADVANCED = "case.stage_advanced"
    RUN_STARTED = "run.started"
    RUN_STATUS_CHANGED = "run.status_changed"
    RUN_STEP_COMPLETED = "run.step_completed"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_DECIDED = "approval.decided"
    ALERT_CREATED = "alert.created"
    ALERT_ACKNOWLEDGED = "alert.acknowledged"
    INSIGHT_REFRESHED = "insight.refreshed"
    INTELLIGENCE_SCAN_COMPLETE = "intelligence.scan_complete"
    SCREEN_INVALIDATE = "screen.invalidate"
    AI_ASSESSMENT = "ai.assessment_complete"


# Maps event types → React Query keys to invalidate on the client
INVALIDATION_HINTS: dict[str, list[str]] = {
    EventType.CASE_OPENED: ["cases", "screen-context"],
    EventType.CASE_STAGE_ADVANCED: ["cases", "screen-context"],
    EventType.RUN_STARTED: ["runs", "screen-context"],
    EventType.RUN_STATUS_CHANGED: ["runs", "approvals", "screen-context"],
    EventType.RUN_STEP_COMPLETED: ["runs"],
    EventType.APPROVAL_REQUESTED: ["approvals", "screen-context"],
    EventType.APPROVAL_DECIDED: ["approvals", "runs", "screen-context"],
    EventType.ALERT_CREATED: ["alerts", "screen-context"],
    EventType.ALERT_ACKNOWLEDGED: ["alerts"],
    EventType.INSIGHT_REFRESHED: ["insights"],
    EventType.INTELLIGENCE_SCAN_COMPLETE: ["insights", "alerts", "screen-context"],
    EventType.AI_ASSESSMENT: ["cases", "ai-assessments", "screen-context"],
}
