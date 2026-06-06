import pytest
from django.contrib.auth import get_user_model

from apps.approvals.models import ApprovalRequest
from apps.approvals.services import ApprovalService, create_approval_request
from apps.executions.models import WorkflowRun
from apps.organizations.models import Organization
from apps.workflows.models import Workflow, WorkflowNode


@pytest.fixture
def run_and_node(db):
    User = get_user_model()
    user = User.objects.create_user(
        username="approvals-owner",
        email="approvals-owner@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Approvals Org", slug="approvals-org")
    workflow = Workflow.objects.create(
        organization=org,
        name="Approval Flow",
        slug="approval-flow",
        created_by=user,
    )
    run = WorkflowRun.objects.create(workflow=workflow, triggered_by=user)
    node = WorkflowNode.objects.create(
        workflow=workflow,
        key="approval_1",
        node_type=WorkflowNode.NodeType.APPROVAL,
        label="Manager Approval",
        config={"sla_hours": 12, "title": "Approve Budget", "approver_group": "finance"},
    )
    return run, node


@pytest.mark.django_db
def test_create_approval_request_uses_node_config_and_context(run_and_node, monkeypatch):
    run, node = run_and_node
    emitted = {}

    def fake_emit_requested(approval):
        emitted["approval_id"] = approval.id

    monkeypatch.setattr("apps.approvals.services.ApprovalService.emit_requested", fake_emit_requested)

    approval = create_approval_request(run, node, {"input": {"employee_id": 1, "cost": 1200}})

    assert approval.title == "Approve Budget"
    assert approval.approver_group == "finance"
    assert approval.payload == {"context_summary": ["employee_id", "cost"]}
    assert emitted["approval_id"] == approval.id


@pytest.mark.django_db
def test_emit_requested_publishes_expected_payload(run_and_node, monkeypatch):
    run, _ = run_and_node
    approval = ApprovalRequest.objects.create(
        run=run,
        node_key="approval_2",
        title="Approve Contract",
        approver_group="legal",
    )
    published = {}

    def fake_publish(**kwargs):
        published.update(kwargs)

    monkeypatch.setattr("apps.approvals.services.publish_domain_event", fake_publish)

    ApprovalService.emit_requested(approval)

    assert published["aggregate_type"] == "approval"
    assert published["aggregate_id"] == approval.id
    assert published["payload"]["approval_id"] == approval.id
    assert published["payload"]["title"] == "Approve Contract"
    assert published["payload"]["approver_group"] == "legal"


@pytest.mark.django_db
def test_emit_decided_includes_actor_and_status(run_and_node, monkeypatch):
    run, _ = run_and_node
    approval = ApprovalRequest.objects.create(
        run=run,
        node_key="approval_3",
        title="Approve Policy",
        status=ApprovalRequest.Status.APPROVED,
    )
    published = {}

    def fake_publish(**kwargs):
        published.update(kwargs)

    monkeypatch.setattr("apps.approvals.services.publish_domain_event", fake_publish)

    ApprovalService.emit_decided(approval, actor_id=77)

    assert published["actor_id"] == 77
    assert published["payload"]["status"] == ApprovalRequest.Status.APPROVED
    assert published["payload"]["run_id"] == str(run.id)
