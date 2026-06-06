from apps.audit.middleware import AuditContextMiddleware, get_current_request


def test_get_current_request_defaults_to_none():
    assert get_current_request() is None


def test_audit_context_middleware_sets_and_clears_request():
    seen = {}

    def get_response(request):
        seen["during"] = get_current_request()
        return "ok"

    middleware = AuditContextMiddleware(get_response)
    request = object()

    response = middleware(request)

    assert response == "ok"
    assert seen["during"] is request
    assert get_current_request() is None
