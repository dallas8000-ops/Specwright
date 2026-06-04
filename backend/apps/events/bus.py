"""
Event bus — publishes domain events to persistence + real-time channel layer.

Each bounded context (case_service, execution_service, …) emits events here;
WebSocket consumers fan out to connected clients per organization.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import DomainEvent
from .types import INVALIDATION_HINTS, EventType, Service

logger = logging.getLogger(__name__)


def publish_domain_event(
    *,
    service: Service | str,
    event_type: EventType | str,
    organization_id: int | None,
    payload: dict[str, Any] | None = None,
    aggregate_type: str = "",
    aggregate_id: str = "",
    correlation_id: str | None = None,
    actor_id: int | None = None,
) -> DomainEvent:
    return EventBus.publish(
        service=service,
        event_type=event_type,
        organization_id=organization_id,
        payload=payload,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        correlation_id=correlation_id,
        actor_id=actor_id,
    )


class EventBus:
    @staticmethod
    def publish(
        *,
        service: Service | str,
        event_type: EventType | str,
        organization_id: int | None,
        payload: dict[str, Any] | None = None,
        aggregate_type: str = "",
        aggregate_id: str = "",
        correlation_id: str | None = None,
        actor_id: int | None = None,
    ) -> DomainEvent:
        service_str = str(service)
        event_str = str(event_type)
        corr = correlation_id or str(uuid.uuid4())
        body = {
            **(payload or {}),
            "actor_id": actor_id,
            "emitted_at": timezone.now().isoformat(),
        }

        record = DomainEvent.objects.create(
            service=service_str,
            event_type=event_str,
            organization_id=organization_id,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            payload=body,
            correlation_id=corr,
        )

        envelope = {
            "id": record.id,
            "service": service_str,
            "event_type": event_str,
            "organization_id": organization_id,
            "aggregate_type": aggregate_type,
            "aggregate_id": str(aggregate_id),
            "payload": body,
            "correlation_id": corr,
            "created_at": record.created_at.isoformat(),
            "invalidate_queries": INVALIDATION_HINTS.get(event_str, []),
        }

        EventBus._broadcast_realtime(organization_id, actor_id, envelope)
        return record

    @staticmethod
    def _broadcast_realtime(
        organization_id: int | None,
        actor_id: int | None,
        envelope: dict,
    ):
        layer = get_channel_layer()
        if not layer:
            logger.warning("No channel layer — realtime broadcast skipped")
            return

        try:
            if organization_id is not None:
                async_to_sync(layer.group_send)(
                    f"org_{organization_id}",
                    {"type": "ops.event", "envelope": envelope},
                )
            if actor_id is not None:
                async_to_sync(layer.group_send)(
                    f"user_{actor_id}",
                    {"type": "ops.event", "envelope": envelope},
                )
            async_to_sync(layer.group_send)(
                "ops_global",
                {"type": "ops.event", "envelope": envelope},
            )
        except Exception:
            logger.exception("Realtime broadcast failed")
