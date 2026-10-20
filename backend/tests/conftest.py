import os

# Must be set BEFORE the app is imported (settings are read at import time).
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db.database import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services import certificate_service  # noqa: E402
from app.services.cache import cache_delete_prefix  # noqa: E402


@pytest.fixture
def db_session():
    """One database transaction per test, rolled back at the end.

    The routes call db.commit(); with join_transaction_mode="create_savepoint"
    those commits only release a SAVEPOINT, so the real transaction is still
    rolled back and tests never leave data behind or affect each other.
    """
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    cache_delete_prefix("courses:list:")

    with TestClient(app) as test_client:
        yield test_client

    cache_delete_prefix("courses:list:")
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def notifications(monkeypatch):
    """Capture certificate notifications instead of queueing real Celery jobs."""
    sent: list[tuple[str, str]] = []

    monkeypatch.setattr(
        certificate_service,
        "_notify",
        lambda email, number: sent.append((email, number)),
    )

    return sent
