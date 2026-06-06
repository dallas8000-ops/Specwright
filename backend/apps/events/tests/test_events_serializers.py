import pytest

from apps.events.models import DomainEvent
from apps.events.serializers import DomainEventSerializer, ServiceHealthSerializer


@pytest.mark.django_db
def test_domain_event_serializer_exposes_expected_fields():
    event = DomainEvent.objects.create(
        service="execution_service",
        event_type="run.started",
        organization_id=11,
        aggregate_type="workflow_run",
        aggregate_id="run-11",
        payload={"k": "v"},
        correlation_id="corr-11",
    )

    data = DomainEventSerializer(event).data

    assert data["service"] == "execution_service"
    assert data["event_type"] == "run.started"
    assert data["organization_id"] == 11
    assert data["aggregate_id"] == "run-11"
    assert data["payload"] == {"k": "v"}


def test_service_health_serializer_validates_payload():
    serializer = ServiceHealthSerializer(data={"name": "events", "status": "ok"})
    assert serializer.is_valid()
    assert serializer.validated_data["name"] == "events"
    assert serializer.validated_data["status"] == "ok"
