from app.core.config import settings
from app.db.redis import redis_client
from tests.helpers import API


def _clear_keys():
    for key in redis_client.scan_iter(match="ratelimit:*"):
        redis_client.delete(key)


def test_login_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)

    _clear_keys()

    try:
        payload = {"email": "nobody@example.com", "password": "whatever123"}

        for _ in range(10):
            response = client.post(f"{API}/auth/login", json=payload)
            assert response.status_code == 401

        blocked = client.post(f"{API}/auth/login", json=payload)

        assert blocked.status_code == 429
        assert "Retry-After" in blocked.headers
    finally:
        _clear_keys()
