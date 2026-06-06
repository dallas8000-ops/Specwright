from apps.events.types import EventType, INVALIDATION_HINTS, Service


def test_service_enum_values_are_stable():
    assert Service.CASE == "case_service"
    assert Service.EXECUTION == "execution_service"
    assert Service.AI == "ai_service"


def test_invalidation_hints_exist_for_runtime_events():
    expected = {
        EventType.RUN_STARTED,
        EventType.RUN_STATUS_CHANGED,
        EventType.APPROVAL_REQUESTED,
        EventType.APPROVAL_DECIDED,
    }
    assert expected.issubset(set(INVALIDATION_HINTS.keys()))


def test_invalidation_hints_values_are_string_lists():
    for keys in INVALIDATION_HINTS.values():
        assert isinstance(keys, list)
        assert all(isinstance(item, str) for item in keys)
