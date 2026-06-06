import pytest
from django.contrib.auth import get_user_model

from apps.approvals.models import ApprovalRequest
from apps.approvals.serializers import ApprovalRequestSerializer
from apps.executions.models import WorkflowRun
from apps.organizations.models import Organization
from apps.workflows.models import Workflow


@pytest.mark.django_db
def test_approval_request_serializer_exposes_names_and_meaning(monkeypatch):
    User = get_user_model()
    creator = User.objects.create_user(
        username="creator",
        email="creator@example.com",
        password="pass12345",
    )
    assignee = User.objects.create_user(
        username="assignee",
        email="assignee@example.com",
        password="pass12345",
        first_name="Ada",
        last_name="Lovelace",
    )
    decider = User.objects.create_user(
        username="decider",
        email="decider@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Serializer Org", slug="serializer-org")
    workflow = Workflow.objects.create(
        organization=org,
        name="Serializer Workflow",
        slug="serializer-workflow",
        created_by=creator,
    )
    run = WorkflowRun.objects.create(workflow=workflow, triggered_by=creator)
    approval = ApprovalRequest.objects.create(
        run=run,
        node_key="approval_1",
        title="Approve Something",
        assigned_to=assignee,
        decided_by=decider,
    )

    monkeypatch.setattr(
        "apps.approvals.serializers.approval_meaning",
        lambda obj: {"severity": "info", "id": obj.id},
    )

    data = ApprovalRequestSerializer(approval).data

    assert data["workflow_name"] == workflow.name
    assert data["run_id"] == str(run.id)
    assert data["assigned_to_name"] == "Ada Lovelace"
    assert data["decided_by_name"] == "decider"
    assert data["meaning"]["severity"] == "info"


@pytest.mark.django_db
def test_approval_request_serializer_handles_missing_users(monkeypatch):
    User = get_user_model()
    creator = User.objects.create_user(
        username="creator2",
        email="creator2@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Serializer Org 2", slug="serializer-org-2")
    workflow = Workflow.objects.create(
        organization=org,
        name="Serializer Workflow 2",
        slug="serializer-workflow-2",
        created_by=creator,
    )
    run = WorkflowRun.objects.create(workflow=workflow, triggered_by=creator)
    approval = ApprovalRequest.objects.create(
        run=run,
        node_key="approval_2",
        title="Approve Another",
    )

    monkeypatch.setattr("apps.approvals.serializers.approval_meaning", lambda obj: {})

    data = ApprovalRequestSerializer(approval).data

    assert data["assigned_to_name"] == ""
    assert data["decided_by_name"] == ""


@pytest.mark.django_db
def test_approval_request_serializer_uses_username_when_assignee_has_no_full_name(monkeypatch):
    User = get_user_model()
    creator = User.objects.create_user(
        username="creator3",
        email="creator3@example.com",
        password="pass12345",
    )
    assignee = User.objects.create_user(
        username="assignee3",
        email="assignee3@example.com",
        password="pass12345",
    )
    org = Organization.objects.create(name="Serializer Org 3", slug="serializer-org-3")
    workflow = Workflow.objects.create(
        organization=org,
        name="Serializer Workflow 3",
        slug="serializer-workflow-3",
        created_by=creator,
    )
    run = WorkflowRun.objects.create(workflow=workflow, triggered_by=creator)
    approval = ApprovalRequest.objects.create(
        run=run,
        node_key="approval_3",
        title="Approve Username Fallback",
        assigned_to=assignee,
    )

    monkeypatch.setattr("apps.approvals.serializers.approval_meaning", lambda obj: {})
    data = ApprovalRequestSerializer(approval).data

    assert data["assigned_to_name"] == "assignee3"
