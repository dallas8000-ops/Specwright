import pytest
from django.contrib.auth import get_user_model

from apps.executions.models import WorkflowRun
from apps.executions.tasks import execute_workflow_run, resume_workflow_run, start_workflow_run
from apps.organizations.models import Organization
from apps.workflows.models import Workflow


@pytest.mark.django_db
def test_start_workflow_run_sets_pending_and_dispatches(monkeypatch):
    User = get_user_model()
    user = User.objects.create_user(
        username="task-owner",
        email="task-owner@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Task Org", slug="task-org")
    workflow = Workflow.objects.create(
        organization=org,
        name="Task Workflow",
        slug="task-workflow",
        created_by=user,
        sla_hours=2,
    )

    delayed = {}
    started = {}

    def fake_delay(run_id):
        delayed["run_id"] = run_id

    def fake_started(run):
        started["run_id"] = str(run.id)

    monkeypatch.setattr("apps.executions.tasks.execute_workflow_run.delay", fake_delay)
    monkeypatch.setattr("apps.executions.tasks.ExecutionService.run_started", fake_started)

    run = start_workflow_run(
        workflow_id=workflow.id,
        triggered_by_id=user.id,
        input_payload={"ticket": "T-1"},
    )

    db_run = WorkflowRun.objects.get(id=run.id)
    assert db_run.status == WorkflowRun.Status.PENDING
    assert db_run.context == {"input": {"ticket": "T-1"}}
    assert db_run.sla_deadline is not None
    assert delayed["run_id"] == str(run.id)
    assert started["run_id"] == str(run.id)


@pytest.mark.django_db
def test_execute_workflow_run_updates_status_and_emits_change(monkeypatch):
    User = get_user_model()
    user = User.objects.create_user(
        username="task-exec",
        email="task-exec@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Task Exec Org", slug="task-exec-org")
    workflow = Workflow.objects.create(
        organization=org,
        name="Task Exec Workflow",
        slug="task-exec-workflow",
        created_by=user,
    )
    run = WorkflowRun.objects.create(
        workflow=workflow,
        triggered_by=user,
        status=WorkflowRun.Status.PENDING,
    )

    class _Engine:
        def __init__(self, run_obj):
            self.run_obj = run_obj

        def run_from(self):
            self.run_obj.status = WorkflowRun.Status.COMPLETED
            self.run_obj.save(update_fields=["status"])

    emitted = {}

    def fake_status_changed(run_obj, node_key=None):
        emitted["run_id"] = str(run_obj.id)
        emitted["node_key"] = node_key

    monkeypatch.setattr("apps.executions.tasks.WorkflowEngine", _Engine)
    monkeypatch.setattr("apps.executions.tasks.ExecutionService.run_status_changed", fake_status_changed)

    result = execute_workflow_run.run(str(run.id))

    run.refresh_from_db()
    assert run.status == WorkflowRun.Status.COMPLETED
    assert result == {"run_id": str(run.id), "status": WorkflowRun.Status.COMPLETED}
    assert emitted["run_id"] == str(run.id)
    assert emitted["node_key"] is None


@pytest.mark.django_db
def test_resume_workflow_run_uses_from_node_and_emits(monkeypatch):
    User = get_user_model()
    user = User.objects.create_user(
        username="task-resume",
        email="task-resume@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Task Resume Org", slug="task-resume-org")
    workflow = Workflow.objects.create(
        organization=org,
        name="Task Resume Workflow",
        slug="task-resume-workflow",
        created_by=user,
    )
    run = WorkflowRun.objects.create(
        workflow=workflow,
        triggered_by=user,
        status=WorkflowRun.Status.WAITING,
    )

    observed = {}

    class _Engine:
        def __init__(self, run_obj):
            self.run_obj = run_obj

        def run_from(self, start_key=None):
            observed["start_key"] = start_key
            self.run_obj.status = WorkflowRun.Status.COMPLETED
            self.run_obj.save(update_fields=["status"])

    emitted = {}

    def fake_status_changed(run_obj, node_key=None):
        emitted["run_id"] = str(run_obj.id)
        emitted["node_key"] = node_key

    monkeypatch.setattr("apps.executions.tasks.WorkflowEngine", _Engine)
    monkeypatch.setattr("apps.executions.tasks.ExecutionService.run_status_changed", fake_status_changed)

    result = resume_workflow_run.run(str(run.id), "approval_1")

    run.refresh_from_db()
    assert observed["start_key"] == "approval_1"
    assert run.status == WorkflowRun.Status.COMPLETED
    assert result == {"run_id": str(run.id), "status": WorkflowRun.Status.COMPLETED}
    assert emitted["run_id"] == str(run.id)
    assert emitted["node_key"] == "approval_1"
