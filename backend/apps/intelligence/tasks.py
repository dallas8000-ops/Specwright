from celery import shared_task

from apps.organizations.models import Organization

from .services import refresh_institutional_memory, scan_proactive_alerts


@shared_task
def run_intelligence_scan():
    for org in Organization.objects.filter(is_active=True):
        refresh_institutional_memory(org)
        scan_proactive_alerts(org)
    return {"organizations_scanned": Organization.objects.filter(is_active=True).count()}
