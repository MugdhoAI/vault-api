from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.config import get_settings


def _cipher() -> MultiFernet:
    settings = get_settings()
    if not settings.encryption_key:
        raise RuntimeError("ENCRYPTION_KEY must be configured")

    previous_keys = [
        key.strip()
        for key in settings.encryption_key_previous.split(",")
        if key.strip()
    ]
    try:
        return MultiFernet(
            [Fernet(key.encode()) for key in [settings.encryption_key, *previous_keys]]
        )
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Encryption key configuration is invalid") from exc


def encrypt_value(value: str) -> str:
    return _cipher().encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    try:
        return _cipher().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Stored secret cannot be decrypted") from exc
