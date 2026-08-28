import pytest
import stripe

from api.services.stripe_resilience import StripeOperationError, call_stripe


@pytest.mark.anyio
async def test_transient_stripe_error_retries_then_recovers():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise stripe.APIError("temporary")
        return "ok"

    result = await call_stripe(
        "test.operation",
        operation,
        max_attempts=3,
        base_delay_seconds=0,
    )

    assert result == "ok"
    assert attempts == 3


@pytest.mark.anyio
async def test_authentication_error_is_not_retried():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        raise stripe.AuthenticationError("bad key")

    with pytest.raises(StripeOperationError) as captured:
        await call_stripe(
            "test.operation",
            operation,
            max_attempts=3,
            base_delay_seconds=0,
        )

    assert captured.value.failure.category == "authentication"
    assert captured.value.failure.retryable is False
    assert attempts == 1
