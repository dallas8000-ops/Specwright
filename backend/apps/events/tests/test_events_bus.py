import pytest

from apps.events.bus import EventBus, publish_domain_event
from apps.events.models import DomainEvent
from apps.events.types import EventType, Service


class _FakeLayer:
    def __init__(self):
        self.calls = []

    def group_send(self, group_name, payload):
        self.calls.append((group_name, payload))


@pytest.mark.django_db
def test_publish_persists_event_and_broadcasts(monkeypatch):
    layer = _FakeLayer()
    monkeypatch.setattr("apps.events.bus.get_channel_layer", lambda: layer)
    monkeypatch.setattr("apps.events.bus.async_to_sync", lambda fn: fn)

    record = EventBus.publish(
        service=Service.EXECUTION,
        event_type=EventType.RUN_STARTED,
        organization_id=42,
        payload={"run_id": "abc"},
        aggregate_type="workflow_run",
        aggregate_id="abc",
        actor_id=9,
        correlation_id="corr-1",
    )

    db_record = DomainEvent.objects.get(id=record.id)
    assert db_record.service == Service.EXECUTION
    assert db_record.event_type == EventType.RUN_STARTED
    assert db_record.organization_id == 42
    assert db_record.aggregate_id == "abc"
    assert db_record.correlation_id == "corr-1"
    assert db_record.payload["run_id"] == "abc"
    assert db_record.payload["actor_id"] == 9

    groups = [name for name, _ in layer.calls]
    assert "org_42" in groups
    assert "user_9" in groups
    assert "ops_global" in groups


@pytest.mark.django_db
def test_publish_handles_missing_channel_layer(monkeypatch):
    warnings = []

    monkeypatch.setattr("apps.events.bus.get_channel_layer", lambda: None)
    monkeypatch.setattr("apps.events.bus.async_to_sync", lambda fn: fn)
    monkeypatch.setattr("apps.events.bus.logger.warning", lambda message: warnings.append(message))

    record = EventBus.publish(
        service=Service.APPROVAL,
        event_type=EventType.APPROVAL_REQUESTED,
        organization_id=None,
        payload={"approval_id": 1},
        aggregate_type="approval",
        aggregate_id="1",
    )

    assert DomainEvent.objects.filter(id=record.id).exists()
    assert warnings == ["No channel layer — realtime broadcast skipped"]


@pytest.mark.django_db
def test_publish_domain_event_wrapper_forwards_to_eventbus(monkeypatch):
    seen = {}

    def fake_publish(**kwargs):
        seen.update(kwargs)
        return "record"

    monkeypatch.setattr("apps.events.bus.EventBus.publish", staticmethod(fake_publish))

    result = publish_domain_event(
        service=Service.CASE,
        event_type=EventType.CASE_OPENED,
        organization_id=5,
        payload={"case_id": 1},
        aggregate_type="case",
        aggregate_id="1",
        correlation_id="c1",
        actor_id=33,
    )

    assert result == "record"
    assert seen["service"] == Service.CASE
    assert seen["event_type"] == EventType.CASE_OPENED
    assert seen["organization_id"] == 5
    assert seen["payload"] == {"case_id": 1}


@pytest.mark.django_db
def test_publish_handles_realtime_broadcast_exception(monkeypatch):
    class _BrokenLayer:
        def group_send(self, group_name, payload):
            raise RuntimeError("channel down")

    layer = _BrokenLayer()
    monkeypatch.setattr("apps.events.bus.get_channel_layer", lambda: layer)
    monkeypatch.setattr("apps.events.bus.async_to_sync", lambda fn: fn)

    record = EventBus.publish(
        service=Service.EXECUTION,
        event_type=EventType.RUN_STATUS_CHANGED,
        organization_id=99,
        payload={"run_id": "r-99"},
        aggregate_type="workflow_run",
        aggregate_id="r-99",
        actor_id=1,
    )

    assert DomainEvent.objects.filter(id=record.id).exists()
