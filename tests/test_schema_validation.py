from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import SecretCreate, SecretUpdate


def test_secret_name_rejects_blank_values() -> None:
    with pytest.raises(ValidationError):
        SecretCreate(name="   ", value="secret-value")

    with pytest.raises(ValidationError):
        SecretUpdate(name="   ")


def test_secret_update_requires_at_least_one_field() -> None:
    with pytest.raises(ValidationError):
        SecretUpdate()

    with pytest.raises(ValidationError):
        SecretUpdate(name=None, value=None)


def test_secret_name_is_trimmed() -> None:
    assert SecretCreate(name="  database  ", value="secret-value").name == "database"
    assert SecretUpdate(name="  database  ").name == "database"
