from apps.events.bus import publish_domain_event
from apps.events.types import EventType, Service

from .models import Case


class CaseService:
    @staticmethod
    def emit_opened(case: Case, *, actor_id: int | None):
        publish_domain_event(
            service=Service.CASE,
            event_type=EventType.CASE_OPENED,
            organization_id=case.organization_id,
            aggregate_type="case",
            aggregate_id=case.id,
            actor_id=actor_id,
            payload={
                "case_id": case.id,
                "title": case.title,
                "case_type": case.case_type,
                "stage": case.stage,
                "priority": case.priority,
            },
        )

    @staticmethod
    def emit_stage_advanced(case: Case, *, actor_id: int | None):
        publish_domain_event(
            service=Service.CASE,
            event_type=EventType.CASE_STAGE_ADVANCED,
            organization_id=case.organization_id,
            aggregate_type="case",
            aggregate_id=case.id,
            actor_id=actor_id,
            payload={
                "case_id": case.id,
                "title": case.title,
                "stage": case.stage,
                "stage_label": case.get_stage_display(),
            },
        )
