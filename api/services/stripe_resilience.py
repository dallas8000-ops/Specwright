"""Safe Stripe retries and sanitized operational diagnostics."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable

import stripe

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StripeFailure:
    category: str
    retryable: bool
    message: str
    status_code: int | None = None
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StripeOperationError(RuntimeError):
    def __init__(self, operation: str, failure: StripeFailure):
        super().__init__(failure.message)
        self.operation = operation
        self.failure = failure


_last_failure: dict[str, Any] | None = None


def classify_stripe_error(exc: stripe.StripeError) -> StripeFailure:
    status = getattr(exc, "http_status", None)
    request_id = getattr(exc, "request_id", None)
    if isinstance(exc, stripe.RateLimitError):
        return StripeFailure("rate_limit", True, "Stripe is rate limiting requests", status, request_id)
    if isinstance(exc, stripe.APIConnectionError):
        return StripeFailure("network", True, "Stripe could not be reached", status, request_id)
    if isinstance(exc, stripe.APIError):
        return StripeFailure("stripe_api", True, "Stripe returned a temporary API error", status, request_id)
    if isinstance(exc, stripe.AuthenticationError):
        return StripeFailure("authentication", False, "Stripe credentials are invalid or expired", status, request_id)
    if isinstance(exc, stripe.PermissionError):
        return StripeFailure("permission", False, "Stripe key lacks a required permission", status, request_id)
    if isinstance(exc, stripe.InvalidRequestError):
        return StripeFailure("invalid_request", False, "Stripe rejected the request configuration", status, request_id)
    if isinstance(exc, stripe.CardError):
        return StripeFailure("payment", False, "The payment method was declined", status, request_id)
    return StripeFailure("stripe", False, "Stripe request failed", status, request_id)


def stripe_health_snapshot() -> dict[str, Any]:
    return {
        "last_failure": dict(_last_failure) if _last_failure else None,
        "policy": {
            "retries": ["rate_limit", "network", "stripe_api"],
            "manual_action": ["authentication", "permission", "invalid_request", "payment"],
        },
    }


async def call_stripe(
    operation: str,
    func: Callable[..., Any],
    *args: Any,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.25,
    **kwargs: Any,
) -> Any:
    """Run a synchronous Stripe SDK call off-loop; retry transient failures only."""
    global _last_failure
    attempts = max(1, max_attempts)
    for attempt in range(1, attempts + 1):
        try:
            result = await asyncio.to_thread(func, *args, **kwargs)
            _last_failure = None
            return result
        except stripe.StripeError as exc:
            failure = classify_stripe_error(exc)
            _last_failure = {
                "operation": operation,
                "category": failure.category,
                "retryable": failure.retryable,
                "status_code": failure.status_code,
                "request_id": failure.request_id,
                "attempt": attempt,
                "at": datetime.now(timezone.utc).isoformat(),
            }
            logger.warning(
                "Stripe operation failed: operation=%s category=%s retryable=%s status=%s request_id=%s attempt=%s",
                operation,
                failure.category,
                failure.retryable,
                failure.status_code,
                failure.request_id,
                attempt,
            )
            if not failure.retryable or attempt >= attempts:
                raise StripeOperationError(operation, failure) from exc
            await asyncio.sleep(base_delay_seconds * (2 ** (attempt - 1)))
