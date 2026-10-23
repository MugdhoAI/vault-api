import asyncio
from typing import Self

import pytest
from cryptography.fernet import Fernet, InvalidToken

from app import crypto
from app.config import Settings
from scripts import rotate_encryption_key as rotation


class FakeSecret:
    def __init__(self, secret_id: int, value: str) -> None:
        self.id = secret_id
        self.value = value


class FakeScalars:
    def __init__(self, records: list[FakeSecret]) -> None:
        self.records = records

    def __iter__(self):
        return iter(self.records)


class FakeTransaction:
    def __init__(self, session: "FakeSession") -> None:
        self.session = session
        self.original_values: list[str] = []

    async def __aenter__(self) -> Self:
        self.original_values = [record.value for record in self.session.records]
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_type is not None:
            for record, original_value in zip(
                self.session.records, self.original_values, strict=True
            ):
                record.value = original_value
        return False


class FakeSession:
    def __init__(self, records: list[FakeSecret]) -> None:
        self.records = records

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
        return False

    def begin(self) -> FakeTransaction:
        return FakeTransaction(self)

    async def scalars(self, statement) -> FakeScalars:
        return FakeScalars(self.records)


def configure_rotation(monkeypatch, new_key: str, previous_key: str) -> None:
    settings = Settings(
        encryption_key=new_key,
        encryption_key_previous=previous_key,
    )
    monkeypatch.setattr(rotation, "get_settings", lambda: settings)
    monkeypatch.setattr(crypto, "get_settings", lambda: settings)


def test_rotation_reencrypts_values_with_the_new_primary_key(monkeypatch) -> None:
    old_key = Fernet.generate_key().decode()
    new_key = Fernet.generate_key().decode()
    plaintexts = ["first-secret", "second-secret"]
    records = [
        FakeSecret(
            index,
            Fernet(old_key.encode()).encrypt(value.encode()).decode(),
        )
        for index, value in enumerate(plaintexts, start=1)
    ]
    session = FakeSession(records)
    configure_rotation(monkeypatch, new_key, old_key)
    monkeypatch.setattr(rotation, "session_factory", lambda: session)

    rotated = asyncio.run(rotation.rotate_encryption_key())

    assert rotated == len(plaintexts)
    for record, plaintext in zip(records, plaintexts, strict=True):
        assert Fernet(new_key.encode()).decrypt(record.value.encode()).decode() == plaintext
        with pytest.raises(InvalidToken):
            Fernet(old_key.encode()).decrypt(record.value.encode())


def test_rotation_failure_does_not_leave_partial_changes(monkeypatch) -> None:
    old_key = Fernet.generate_key().decode()
    new_key = Fernet.generate_key().decode()
    first_value = Fernet(old_key.encode()).encrypt(b"first-secret").decode()
    records = [
        FakeSecret(1, first_value),
        FakeSecret(2, "not-a-valid-fernet-token"),
    ]
    original_values = [record.value for record in records]
    session = FakeSession(records)
    configure_rotation(monkeypatch, new_key, old_key)
    monkeypatch.setattr(rotation, "session_factory", lambda: session)

    with pytest.raises(ValueError, match="Stored secret cannot be decrypted"):
        asyncio.run(rotation.rotate_encryption_key())

    assert [record.value for record in records] == original_values


def test_rotation_requires_at_least_one_previous_key(monkeypatch) -> None:
    settings = Settings(encryption_key=Fernet.generate_key().decode())
    monkeypatch.setattr(rotation, "get_settings", lambda: settings)

    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY_PREVIOUS"):
        asyncio.run(rotation.rotate_encryption_key())


def test_rotation_rejects_current_key_in_previous_key_list(monkeypatch) -> None:
    key = Fernet.generate_key().decode()
    settings = Settings(
        encryption_key=key,
        encryption_key_previous=key,
    )
    monkeypatch.setattr(rotation, "get_settings", lambda: settings)

    with pytest.raises(RuntimeError, match="must differ from previous keys"):
        asyncio.run(rotation.rotate_encryption_key())
