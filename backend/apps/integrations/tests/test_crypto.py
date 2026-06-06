from cryptography.fernet import InvalidToken
from django.test import override_settings
import pytest

from apps.integrations.crypto import decrypt_secrets, encrypt_secrets


@override_settings(INTEGRATION_CREDENTIALS_KEY="test-key-1")
def test_encrypt_decrypt_round_trip():
    payload = {"api_key": "secret", "nested": {"enabled": True}}

    blob = encrypt_secrets(payload)

    assert isinstance(blob, bytes)
    assert decrypt_secrets(blob) == payload


def test_decrypt_fails_with_different_key():
    payload = {"token": "abc"}

    with override_settings(INTEGRATION_CREDENTIALS_KEY="first-key"):
        blob = encrypt_secrets(payload)

    with override_settings(INTEGRATION_CREDENTIALS_KEY="second-key"):
        with pytest.raises(InvalidToken):
            decrypt_secrets(blob)


def test_encrypt_decrypt_works_with_equivalent_32_char_prefixes():
    payload = {"k": "v"}
    base = "a" * 32

    with override_settings(INTEGRATION_CREDENTIALS_KEY=base + "-suffix-one"):
        blob = encrypt_secrets(payload)

    with override_settings(INTEGRATION_CREDENTIALS_KEY=base + "-suffix-two"):
        assert decrypt_secrets(blob) == payload
