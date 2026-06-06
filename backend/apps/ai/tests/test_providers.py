import pytest
from django.test import override_settings

from apps.ai import providers


def test_parse_json_extracts_embedded_object():
    text = "noise before {\"ok\": true, \"count\": 2} noise after"
    parsed = providers._parse_json(text)
    assert parsed == {"ok": True, "count": 2}


def test_parse_json_raises_for_invalid_payload():
    with pytest.raises(Exception):
        providers._parse_json("not-json")


@override_settings(AI_API_KEY="")
def test_call_llm_returns_none_without_key():
    assert providers.call_llm(system="s", user="u") is None


@override_settings(AI_API_KEY="key", AI_API_BASE_URL="https://llm.test", AI_MODEL="model-x")
def test_call_llm_success_path(monkeypatch):
    captured = {}

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "{\"answer\": 42}"}}]}

    class _Client:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, headers, json):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return _Response()

    monkeypatch.setattr("apps.ai.providers.httpx.Client", _Client)

    result = providers.call_llm(system="system prompt", user="user prompt")

    assert result == {"answer": 42}
    assert captured["url"] == "https://llm.test/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer key"
    assert captured["json"]["model"] == "model-x"
    assert captured["json"]["messages"][0]["content"] == "system prompt"


@override_settings(AI_API_KEY="key")
def test_call_llm_handles_client_exception(monkeypatch):
    class _Client:
        def __init__(self, timeout):
            pass

        def __enter__(self):
            raise RuntimeError("boom")

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("apps.ai.providers.httpx.Client", _Client)

    assert providers.call_llm(system="s", user="u") is None


def test_heuristic_triage_legal_intake_high_priority():
    result = providers.heuristic_triage(
        "legal",
        {"priority": "high", "stage": "intake", "title": "MSA Negotiation"},
    )

    assert result["provider"] == "heuristic"
    assert result["suggested_stage_advance"] is True
    assert "Complete intake validation" in result["recommended_action"]
    assert len(result["risks"]) >= 2
