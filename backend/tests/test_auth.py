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


class TestRefresh:
    """Tests for POST /api/auth/refresh — token rotation and CSRF."""

    def _setup_user(self, test_client: TestClient, email: str = "refresh@test.com") -> None:
        """Register and login a user. The TestClient cookie jar retains
        the httpOnly refresh_token cookie for subsequent requests."""
        test_client.post(
            "/api/auth/register",
            json={"email": email, "username": email.split("@")[0], "password": "TestPass123"},
        )
        test_client.post(
            "/api/auth/login",
            json={"email": email, "password": "TestPass123"},
        )

    def test_refresh_success(self, test_client: TestClient):
        """A valid refresh token + CSRF header should return a new access token."""
        self._setup_user(test_client)
        resp = test_client.post("/api/auth/refresh", headers={"X-CSRF-Protection": "1"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_refresh_missing_csrf(self, test_client: TestClient):
        """Missing X-CSRF-Protection header should return 401."""
        self._setup_user(test_client)
        resp = test_client.post("/api/auth/refresh")  # No CSRF header
        assert resp.status_code == 401

    def test_refresh_no_cookie(self, test_client: TestClient):
        """No refresh_token cookie should return 401."""
        # Note: no _setup_user → no cookies
        resp = test_client.post("/api/auth/refresh", headers={"X-CSRF-Protection": "1"})
        assert resp.status_code == 401

    def test_refresh_reuse_detection(self, test_client: TestClient):
        """Presenting a revoked refresh token should revoke the entire family."""
        self._setup_user(test_client)

        # Capture the current refresh token value
        old_cookie = test_client.cookies.get("refresh_token")

        # First refresh — rotates the token (old one is now revoked)
        resp1 = test_client.post("/api/auth/refresh", headers={"X-CSRF-Protection": "1"})
        assert resp1.status_code == 200

        # Manually restore the old (now revoked) token
        test_client.cookies.set("refresh_token", old_cookie)

        # Second refresh with the revoked token → reuse detected
        resp2 = test_client.post("/api/auth/refresh", headers={"X-CSRF-Protection": "1"})
        assert resp2.status_code == 401


class TestLogout:
    """Tests for POST /api/auth/logout — token revocation."""

    def _setup_and_get_token(self, test_client: TestClient) -> str:
        test_client.post(
            "/api/auth/register",
            json={"email": "logout@test.com", "username": "logout", "password": "TestPass123"},
        )
        resp = test_client.post(
            "/api/auth/login",
            json={"email": "logout@test.com", "password": "TestPass123"},
        )
        return resp.json()["access_token"]

    def test_logout_success(self, test_client: TestClient):
        """A valid logout should revoke tokens and return 204."""
        token = self._setup_and_get_token(test_client)
        resp = test_client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 204

    def test_logout_unauthenticated(self, test_client: TestClient):
        """Logout without a token should return 401."""
        resp = test_client.post("/api/auth/logout")
        assert resp.status_code == 401
