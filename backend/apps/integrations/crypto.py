import json

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet() -> Fernet:
    key = settings.INTEGRATION_CREDENTIALS_KEY.encode()[:32]
    import base64
    import hashlib

    digest = hashlib.sha256(key).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secrets(data: dict) -> bytes:
    return _fernet().encrypt(json.dumps(data).encode())


def decrypt_secrets(blob: bytes) -> dict:
    return json.loads(_fernet().decrypt(blob).decode())
