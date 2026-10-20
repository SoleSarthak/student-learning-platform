from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_is_not_plaintext_and_verifies():
    hashed = hash_password("CorrectHorse123")

    assert hashed != "CorrectHorse123"
    assert verify_password("CorrectHorse123", hashed)
    assert not verify_password("wrong-password", hashed)


def test_token_round_trip():
    assert decode_access_token(create_access_token(42)) == 42


@pytest.mark.parametrize("bad_token", ["", "garbage", "a.b.c"])
def test_malformed_token_raises_value_error(bad_token):
    with pytest.raises(ValueError):
        decode_access_token(bad_token)


def test_expired_token_raises_value_error():
    expired = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    with pytest.raises(ValueError):
        decode_access_token(expired)


def test_token_signed_with_other_key_is_rejected():
    forged = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        "some-other-secret-key-that-is-long-enough-123",
        algorithm="HS256",
    )

    with pytest.raises(ValueError):
        decode_access_token(forged)
