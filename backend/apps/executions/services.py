from apps.events.bus import publish_domain_event
from apps.events.types import EventType, Service

from .models import WorkflowRun


class ExecutionService:
    @staticmethod
    def emit_run_event(run: WorkflowRun, event_type: EventType, *, extra: dict | None = None):
        org_id = run.workflow.organization_id
        payload = {
            "run_id": str(run.id),
            "workflow_slug": run.workflow.slug,
            "workflow_name": run.workflow.name,
            "status": run.status,
            "trigger_source": run.trigger_source,
            **(extra or {}),
        }
        publish_domain_event(
            service=Service.EXECUTION,
            event_type=event_type,
            organization_id=org_id,
            aggregate_type="workflow_run",
            aggregate_id=str(run.id),
            actor_id=run.triggered_by_id,
            payload=payload,
        )

    @staticmethod
    def run_started(run: WorkflowRun):
        ExecutionService.emit_run_event(run, EventType.RUN_STARTED)

    @staticmethod
    def run_status_changed(run: WorkflowRun, *, node_key: str | None = None):
        ExecutionService.emit_run_event(
            run,
            EventType.RUN_STATUS_CHANGED,
            extra={"node_key": node_key, "error_message": run.error_message[:200] if run.error_message else ""},
        )

    @staticmethod
    def step_completed(run: WorkflowRun, *, node_key: str, node_type: str, status: str):
        ExecutionService.emit_run_event(
            run,
            EventType.RUN_STEP_COMPLETED,
            extra={"node_key": node_key, "node_type": node_type, "step_status": status},
        )
