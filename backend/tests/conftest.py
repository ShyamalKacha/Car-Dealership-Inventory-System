"""
pytest fixtures for the Car Dealership API.

Uses a dedicated test PostgreSQL database (car_dealership_test).
Each test function gets its own transaction, rolled back after completion
so tests never leak data to one another.
"""

import os
from urllib.parse import urlparse, urlunparse

os.environ["TESTING"] = "1"  # Disable rate limiting during tests

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.database import Base
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.user import User

# Derive test DB URL from the main DATABASE_URL — swap the database name
parsed = urlparse(str(settings.DATABASE_URL))
test_path = parsed.path.rsplit("/", 1)[0] + "/car_dealership_test"
TEST_DATABASE_URL = urlunparse(parsed._replace(path=test_path))


# ---------------------------------------------------------------------------
# Session-scoped engine — tables created once, dropped at end
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Per-test DB session — transaction is rolled back after each test
# ---------------------------------------------------------------------------
@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Test client with overridden DB dependency
# ---------------------------------------------------------------------------
@pytest.fixture
def test_client(test_engine):
    app = create_app()

    def _get_test_db():
        connection = test_engine.connect()
        transaction = connection.begin()
        session = Session(bind=connection)
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()
            connection.close()

    app.dependency_overrides[get_db] = _get_test_db

    with TestClient(app) as client:
        yield client


# ---------------------------------------------------------------------------
# Sample users
# ---------------------------------------------------------------------------
@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("TestPass123"),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=hash_password("AdminPass123"),
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Auth headers
# ---------------------------------------------------------------------------
@pytest.fixture
def user_token(test_user: User) -> str:
    return create_access_token(test_user.id, test_user.role)


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(admin_user.id, admin_user.role)


@pytest.fixture
def user_headers(user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}
