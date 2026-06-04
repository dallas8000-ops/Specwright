from .middleware import get_current_request
from .models import AuditLog


def log_action(*, action: str, resource_type: str, resource_id: str, metadata: dict | None = None):
    request = get_current_request()
    actor = getattr(request, "user", None) if request else None
    if actor and not actor.is_authenticated:
        actor = None
    AuditLog.objects.create(
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        organization_id=metadata.pop("organization_id", None) if metadata else None,
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:512] if request else ""),
        metadata=metadata or {},
    )
