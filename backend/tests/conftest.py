"""
pytest fixtures for the Car Dealership API.

Uses a dedicated test PostgreSQL database (car_dealership_test).
Tables are truncated before each test for full isolation.
"""

from urllib.parse import urlparse, urlunparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.database import Base
from app.core.rate_limiter import reset_rate_limiter
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.user import User

# Derive test DB URL from the main DATABASE_URL — swap the database name
parsed = urlparse(str(settings.DATABASE_URL))
test_path = parsed.path.rsplit("/", 1)[0] + "/car_dealership_test"
TEST_DATABASE_URL = urlunparse(parsed._replace(path=test_path))

# Cookies use http in tests, not https
settings.COOKIE_SECURE = False


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
# Clean all rows before each test
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_tables(test_engine):
    with test_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()
    reset_rate_limiter()
    yield


# ---------------------------------------------------------------------------
# Test client with overridden DB dependency
# ---------------------------------------------------------------------------
@pytest.fixture
def test_client(test_engine):
    app = create_app()

    def _get_test_db():
        connection = test_engine.connect()
        session = Session(bind=connection)
        try:
            yield session
            session.commit()
        finally:
            session.close()
            connection.close()

    app.dependency_overrides[get_db] = _get_test_db

    with TestClient(app) as client:
        yield client


# ---------------------------------------------------------------------------
# Sample users (for tests that need pre-existing users, e.g. vehicle tests)
# ---------------------------------------------------------------------------
@pytest.fixture
def test_user(test_engine) -> User:
    connection = test_engine.connect()
    session = Session(bind=connection)
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("TestPass123"),
        role="user",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()
    connection.close()
    return user


@pytest.fixture
def admin_user(test_engine) -> User:
    connection = test_engine.connect()
    session = Session(bind=connection)
    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=hash_password("AdminPass123"),
        role="admin",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()
    connection.close()
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
