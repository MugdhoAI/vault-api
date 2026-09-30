from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _cipher() -> Fernet:
    key = get_settings().encryption_key
    if not key:
        raise RuntimeError("ENCRYPTION_KEY must be configured")
    return Fernet(key.encode())


def encrypt_value(value: str) -> str:
    return _cipher().encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    try:
        return _cipher().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Stored secret cannot be decrypted") from exc
