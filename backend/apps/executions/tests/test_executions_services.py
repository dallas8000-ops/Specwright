import pytest
from django.contrib.auth import get_user_model

from apps.events.types import EventType
from apps.executions.models import WorkflowRun
from apps.executions.services import ExecutionService
from apps.organizations.models import Organization
from apps.workflows.models import Workflow


@pytest.fixture
def run_fixture(db):
    User = get_user_model()
    user = User.objects.create_user(
        username="execution-owner",
        email="execution-owner@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Execution Org", slug="execution-org")
    workflow = Workflow.objects.create(
        organization=org,
        name="Exec Flow",
        slug="exec-flow",
        created_by=user,
    )
    run = WorkflowRun.objects.create(
        workflow=workflow,
        triggered_by=user,
        trigger_source="manual",
        status=WorkflowRun.Status.RUNNING,
    )
    return run


@pytest.mark.django_db
def test_emit_run_event_builds_payload_and_calls_bus(run_fixture, monkeypatch):
    run = run_fixture
    published = {}

    def fake_publish(**kwargs):
        published.update(kwargs)

    monkeypatch.setattr("apps.executions.services.publish_domain_event", fake_publish)

    ExecutionService.emit_run_event(run, EventType.RUN_STARTED, extra={"k": "v"})

    assert published["aggregate_type"] == "workflow_run"
    assert published["aggregate_id"] == str(run.id)
    assert published["actor_id"] == run.triggered_by_id
    assert published["payload"]["run_id"] == str(run.id)
    assert published["payload"]["workflow_slug"] == run.workflow.slug
    assert published["payload"]["k"] == "v"


@pytest.mark.django_db
def test_run_started_emits_started_event(run_fixture, monkeypatch):
    run = run_fixture
    captured = {}

    def fake_emit(run_obj, event_type, extra=None):
        captured["run_id"] = run_obj.id
        captured["event_type"] = event_type
        captured["extra"] = extra

    monkeypatch.setattr("apps.executions.services.ExecutionService.emit_run_event", fake_emit)

    ExecutionService.run_started(run)

    assert captured["run_id"] == run.id
    assert captured["event_type"] == EventType.RUN_STARTED
    assert captured["extra"] is None


@pytest.mark.django_db
def test_run_status_changed_truncates_error_message(run_fixture, monkeypatch):
    run = run_fixture
    run.error_message = "x" * 250
    captured = {}

    def fake_emit(run_obj, event_type, extra=None):
        captured["event_type"] = event_type
        captured["extra"] = extra

    monkeypatch.setattr("apps.executions.services.ExecutionService.emit_run_event", fake_emit)

    ExecutionService.run_status_changed(run, node_key="node-a")

    assert captured["event_type"] == EventType.RUN_STATUS_CHANGED
    assert captured["extra"]["node_key"] == "node-a"
    assert len(captured["extra"]["error_message"]) == 200


@pytest.mark.django_db
def test_step_completed_passes_node_details(run_fixture, monkeypatch):
    run = run_fixture
    captured = {}

    def fake_emit(run_obj, event_type, extra=None):
        captured["event_type"] = event_type
        captured["extra"] = extra

    monkeypatch.setattr("apps.executions.services.ExecutionService.emit_run_event", fake_emit)

    ExecutionService.step_completed(run, node_key="step-1", node_type="integration", status="completed")

    assert captured["event_type"] == EventType.RUN_STEP_COMPLETED
    assert captured["extra"] == {
        "node_key": "step-1",
        "node_type": "integration",
        "step_status": "completed",
    }
