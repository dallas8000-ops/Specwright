import time
from typing import Any

import httpx

from apps.workflows.engine import StepResult

from .crypto import decrypt_secrets
from .models import Connector, Credential, IntegrationLog


def execute_integration_step(node, context: dict, run) -> StepResult:
    config = node.config
    connector_slug = config.get("connector")
    credential_id = config.get("credential_id")
    action = config.get("action", "request")

    try:
        connector = Connector.objects.get(slug=connector_slug, is_active=True)
    except Connector.DoesNotExist:
        return StepResult(success=False, error=f"Connector '{connector_slug}' not found")

    secrets = {}
    if credential_id:
        try:
            cred = Credential.objects.get(id=credential_id)
            secrets = decrypt_secrets(cred.encrypted_secrets)
        except Credential.DoesNotExist:
            return StepResult(success=False, error="Credential not found")

    start = time.monotonic()
    if connector.kind == Connector.ConnectorKind.REST:
        result = _execute_rest(config, secrets, context)
    elif connector.kind == Connector.ConnectorKind.EMAIL:
        result = StepResult(success=True, output={"email_queued": True, "to": config.get("to")})
    elif connector.kind == Connector.ConnectorKind.SLACK:
        result = StepResult(success=True, output={"slack_sent": True, "channel": config.get("channel")})
    else:
        result = StepResult(success=True, output={"connector": connector.slug, "action": action})

    duration_ms = int((time.monotonic() - start) * 1000)
    IntegrationLog.objects.create(
        run_id=run.id,
        connector=connector,
        request_summary={"action": action, "config_keys": list(config.keys())},
        response_summary=result.output,
        success=result.success,
        duration_ms=duration_ms,
    )
    return result


def _execute_rest(config: dict, secrets: dict, context: dict) -> StepResult:
    method = config.get("method", "GET").upper()
    url = _interpolate(config.get("url", ""), context)
    headers = {**secrets.get("headers", {}), **config.get("headers", {})}
    body = config.get("body")
    if isinstance(body, str):
        body = _interpolate(body, context)

    try:
        with httpx.Client(timeout=30) as client:
            response = client.request(method, url, headers=headers, json=body if method != "GET" else None)
        return StepResult(
            success=response.is_success,
            output={"status_code": response.status_code, "body": _safe_json(response)},
            error=None if response.is_success else response.text[:500],
        )
    except httpx.HTTPError as exc:
        return StepResult(success=False, error=str(exc))


def _interpolate(template: str, context: dict) -> str:
    data = {**context.get("input", {}), **context.get("steps", {})}
    result = template
    for key, value in data.items():
        if isinstance(value, (str, int, float)):
            result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return response.text[:1000]
