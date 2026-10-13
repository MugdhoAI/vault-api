"""Re-encrypt stored secrets with the current Fernet key.

Set ENCRYPTION_KEY to the new key and ENCRYPTION_KEY_PREVIOUS to the old key(s)
before running this command. Back up the database and key material first.
"""

import asyncio

from sqlalchemy import select

from app.config import get_settings
from app.crypto import decrypt_value, encrypt_value
from app.db import engine, session_factory
from app.models import Secret


async def rotate_encryption_key() -> int:
    settings = get_settings()
    previous_keys = [
        key.strip()
        for key in settings.encryption_key_previous.split(",")
        if key.strip()
    ]
    if not previous_keys:
        raise RuntimeError("Set ENCRYPTION_KEY_PREVIOUS before rotating stored secrets")
    if settings.encryption_key in previous_keys:
        raise RuntimeError("The new ENCRYPTION_KEY must differ from previous keys")

    rotated = 0
    async with session_factory() as session, session.begin():
        secrets = await session.scalars(
            select(Secret).order_by(Secret.id).with_for_update()
        )
        for secret in secrets:
            plaintext = decrypt_value(secret.value)
            secret.value = encrypt_value(plaintext)
            rotated += 1

    return rotated


async def main() -> None:
    try:
        count = await rotate_encryption_key()
    finally:
        await engine.dispose()
    print(f"Re-encrypted {count} secret values.")


if __name__ == "__main__":
    asyncio.run(main())
