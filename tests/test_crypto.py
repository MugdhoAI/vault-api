from cryptography.fernet import Fernet

from app import crypto
from app.config import Settings


def test_previous_key_can_decrypt_and_new_key_encrypts(monkeypatch) -> None:
    old_key = Fernet.generate_key().decode()
    new_key = Fernet.generate_key().decode()
    old_ciphertext = Fernet(old_key.encode()).encrypt(b"existing-secret").decode()

    monkeypatch.setattr(
        crypto,
        "get_settings",
        lambda: Settings(
            encryption_key=new_key,
            encryption_key_previous=old_key,
        ),
    )

    assert crypto.decrypt_value(old_ciphertext) == "existing-secret"

    new_ciphertext = crypto.encrypt_value("rotated-secret")
    assert Fernet(new_key.encode()).decrypt(new_ciphertext.encode()) == b"rotated-secret"
