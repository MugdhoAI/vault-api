from app.security import create_access_token, decode_subject, hash_password, verify_password


def test_password_hash_is_not_plaintext() -> None:
    password = "correct horse battery staple"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong password", hashed)


def test_access_token_round_trip() -> None:
    token = create_access_token("user@example.com")
    assert decode_subject(token) == "user@example.com"
