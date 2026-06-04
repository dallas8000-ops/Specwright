from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.workflows.engine import WorkflowEngine
from apps.workflows.models import Workflow

from .models import WorkflowRun
from .services import ExecutionService


def start_workflow_run(*, workflow_id: int, triggered_by_id: int | None, input_payload: dict):
    workflow = Workflow.objects.get(id=workflow_id)
    run = WorkflowRun.objects.create(
        workflow=workflow,
        triggered_by_id=triggered_by_id,
        trigger_source="manual",
        context={"input": input_payload},
        status=WorkflowRun.Status.PENDING,
    )
    if workflow.sla_hours:
        run.sla_deadline = timezone.now() + timedelta(hours=workflow.sla_hours)
        run.save(update_fields=["sla_deadline"])
    execute_workflow_run.delay(str(run.id))
    ExecutionService.run_started(run)
    return run


@shared_task(bind=True, max_retries=3)
def execute_workflow_run(self, run_id: str):
    run = WorkflowRun.objects.select_related("workflow").get(id=run_id)
    run.status = WorkflowRun.Status.RUNNING
    run.save(update_fields=["status"])
    engine = WorkflowEngine(run)
    engine.run_from()
    run.refresh_from_db()
    ExecutionService.run_status_changed(run)
    return {"run_id": run_id, "status": run.status}


@shared_task
def resume_workflow_run(run_id: str, from_node_key: str):
    run = WorkflowRun.objects.select_related("workflow").get(id=run_id)
    run.status = WorkflowRun.Status.RUNNING
    run.save(update_fields=["status"])
    engine = WorkflowEngine(run)
    engine.run_from(start_key=from_node_key)
    run.refresh_from_db()
    ExecutionService.run_status_changed(run, node_key=from_node_key)
    return {"run_id": run_id, "status": run.status}
