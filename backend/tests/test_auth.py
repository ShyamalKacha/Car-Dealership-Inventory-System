"""
GREEN tests for the Auth module.

These tests should pass once the auth service and routes are implemented.
"""

import pytest
from fastapi.testclient import TestClient


class TestRegister:
    def test_register_success(self, test_client: TestClient):
        """A valid registration should return 201 with user data."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass1",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["role"] == "user"
        assert "id" in data

    def test_register_duplicate_email(self, test_client: TestClient):
        """Registering with an existing email should return 409 Conflict."""
        test_client.post(
            "/api/auth/register",
            json={
                "email": "dup@example.com",
                "username": "user1",
                "password": "SecurePass1",
            },
        )
        response = test_client.post(
            "/api/auth/register",
            json={
                "email": "dup@example.com",
                "username": "user2",
                "password": "SecurePass1",
            },
        )
        assert response.status_code == 409

    def test_register_admin_with_valid_key(
        self, test_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        """Providing the correct admin_key should create an admin user."""
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_SECRET_KEY",
            "test-admin-key-32-chars-minimum!",
        )
        response = test_client.post(
            "/api/auth/register",
            json={
                "email": "admin@example.com",
                "username": "adminuser",
                "password": "AdminPass1",
                "admin_key": "test-admin-key-32-chars-minimum!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "admin"

    def test_register_admin_with_invalid_key(
        self, test_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        """An incorrect admin_key should create a regular user."""
        monkeypatch.setattr(
            "app.core.config.settings.ADMIN_SECRET_KEY", "real-key"
        )
        response = test_client.post(
            "/api/auth/register",
            json={
                "email": "regular@example.com",
                "username": "regular",
                "password": "UserPass1",
                "admin_key": "wrong-key",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "user"

    @pytest.mark.parametrize(
        "password",
        [
            "short",  # too short
            "nonumber",  # no digit
            "12345678",  # no letter
        ],
    )
    def test_register_weak_password(
        self, test_client: TestClient, password: str
    ):
        """Weak passwords should be rejected with 422."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "password": password,
            },
        )
        assert response.status_code == 422

    def test_register_invalid_email(self, test_client: TestClient):
        """Malformed emails should be rejected with 422."""
        response = test_client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "username": "bademail",
                "password": "SecurePass1",
            },
        )
        assert response.status_code == 422


class TestLogin:
    def test_login_success(self, test_client: TestClient):
        """Valid credentials should return an access token."""
        # Register a user first
        test_client.post(
            "/api/auth/register",
            json={
                "email": "logintest@example.com",
                "username": "logintest",
                "password": "TestPass123",
            },
        )
        # Now login
        response = test_client.post(
            "/api/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "TestPass123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, test_client: TestClient):
        """Wrong password should return 401."""
        test_client.post(
            "/api/auth/register",
            json={
                "email": "wrongpass@example.com",
                "username": "wrongpass",
                "password": "RealPass1",
            },
        )
        response = test_client.post(
            "/api/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPassword1",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, test_client: TestClient):
        """Non-existent email should return 401 (same message as wrong password)."""
        response = test_client.post(
            "/api/auth/login",
            json={
                "email": "nobody@example.com",
                "password": "SomePass1",
            },
        )
        assert response.status_code == 401

    def test_login_empty_fields(self, test_client: TestClient):
        """Empty credentials should return 422."""
        response = test_client.post(
            "/api/auth/login",
            json={"email": "", "password": ""},
        )
        assert response.status_code == 422
