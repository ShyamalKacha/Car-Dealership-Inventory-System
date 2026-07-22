"""
RED tests for the Vehicles module (CRUD + inventory).

These tests will FAIL because vehicle routes and services are stubs
that raise NotImplementedError.
"""

import pytest
from fastapi.testclient import TestClient

VEHICLE_PAYLOAD = {
    "make": "Toyota",
    "model": "Camry",
    "category": "SEDAN",
    "price": 25000.00,
    "quantity": 10,
}


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
class TestCreateVehicle:
    def test_create_as_admin(self, test_client: TestClient, admin_headers: dict):
        resp = test_client.post(
            "/api/vehicles", json=VEHICLE_PAYLOAD, headers=admin_headers
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["make"] == "Toyota"
        assert data["model"] == "Camry"
        assert data["category"] == "SEDAN"
        assert float(data["price"]) == 25000.00
        assert data["quantity"] == 10
        assert "id" in data

    def test_create_as_user(self, test_client: TestClient, user_headers: dict):
        resp = test_client.post(
            "/api/vehicles", json=VEHICLE_PAYLOAD, headers=user_headers
        )
        assert resp.status_code == 403

    def test_create_unauthenticated(self, test_client: TestClient):
        resp = test_client.post("/api/vehicles", json=VEHICLE_PAYLOAD)
        assert resp.status_code == 401

    def test_create_invalid_data(self, test_client: TestClient, admin_headers: dict):
        resp = test_client.post(
            "/api/vehicles",
            json={"make": "", "model": "", "category": "INVALID", "price": -1, "quantity": -1},
            headers=admin_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# LIST
# ---------------------------------------------------------------------------
class TestListVehicles:
    def _seed(self, client: TestClient, headers: dict) -> None:
        client.post("/api/vehicles", json=VEHICLE_PAYLOAD, headers=headers)
        client.post(
            "/api/vehicles",
            json={**VEHICLE_PAYLOAD, "make": "Honda", "model": "Civic"},
            headers=headers,
        )

    def test_list_all(self, test_client: TestClient, admin_headers: dict, user_headers: dict):
        self._seed(test_client, admin_headers)
        resp = test_client.get("/api/vehicles", headers=user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_list_empty(self, test_client: TestClient, user_headers: dict):
        resp = test_client.get("/api/vehicles", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# SEARCH
# ---------------------------------------------------------------------------
class TestSearchVehicles:
    def _seed(self, client: TestClient, headers: dict) -> None:
        for v in [
            {"make": "Toyota", "model": "Camry", "category": "SEDAN", "price": 25000, "quantity": 5},
            {"make": "Honda", "model": "Civic", "category": "SEDAN", "price": 22000, "quantity": 3},
            {"make": "Ford", "model": "F-150", "category": "TRUCK", "price": 35000, "quantity": 2},
            {"make": "Toyota", "model": "RAV4", "category": "SUV", "price": 30000, "quantity": 7},
        ]:
            client.post("/api/vehicles", json=v, headers=headers)

    def test_search_by_make(self, test_client: TestClient, admin_headers: dict, user_headers: dict):
        self._seed(test_client, admin_headers)
        resp = test_client.get("/api/vehicles/search?make=Toyota", headers=user_headers)
        assert resp.status_code == 200
        assert all(v["make"] == "Toyota" for v in resp.json())

    def test_search_by_model(self, test_client: TestClient, admin_headers: dict, user_headers: dict):
        self._seed(test_client, admin_headers)
        resp = test_client.get("/api/vehicles/search?model=Civic", headers=user_headers)
        assert resp.status_code == 200
        assert all(v["model"] == "Civic" for v in resp.json())

    def test_search_by_category(self, test_client: TestClient, admin_headers: dict, user_headers: dict):
        self._seed(test_client, admin_headers)
        resp = test_client.get("/api/vehicles/search?category=TRUCK", headers=user_headers)
        assert resp.status_code == 200
        assert all(v["category"] == "TRUCK" for v in resp.json())

    def test_search_by_price_range(self, test_client: TestClient, admin_headers: dict, user_headers: dict):
        self._seed(test_client, admin_headers)
        resp = test_client.get(
            "/api/vehicles/search?price_min=20000&price_max=26000",
            headers=user_headers,
        )
        assert resp.status_code == 200
        for v in resp.json():
            assert 20000 <= float(v["price"]) <= 26000

    def test_search_combined(self, test_client: TestClient, admin_headers: dict, user_headers: dict):
        self._seed(test_client, admin_headers)
        resp = test_client.get(
            "/api/vehicles/search?make=Toyota&category=SUV&price_min=25000",
            headers=user_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["model"] == "RAV4"

    def test_search_no_results(self, test_client: TestClient, admin_headers: dict, user_headers: dict):
        self._seed(test_client, admin_headers)
        resp = test_client.get("/api/vehicles/search?make=Mazda", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_search_no_params_returns_all(
        self, test_client: TestClient, admin_headers: dict, user_headers: dict
    ):
        self._seed(test_client, admin_headers)
        resp = test_client.get("/api/vehicles/search", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 4


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
class TestUpdateVehicle:
    def _seed(self, client: TestClient, headers: dict) -> int:
        resp = client.post("/api/vehicles", json=VEHICLE_PAYLOAD, headers=headers)
        return resp.json()["id"]

    def test_update_as_admin(self, test_client: TestClient, admin_headers: dict):
        vid = self._seed(test_client, admin_headers)
        resp = test_client.put(
            f"/api/vehicles/{vid}",
            json={"price": 26000, "quantity": 8},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["price"]) == 26000
        assert data["quantity"] == 8
        assert data["make"] == "Toyota"  # unchanged fields preserved

    def test_update_as_user(self, test_client: TestClient, admin_headers: dict, user_headers: dict):
        vid = self._seed(test_client, admin_headers)
        resp = test_client.put(
            f"/api/vehicles/{vid}",
            json={"price": 26000},
            headers=user_headers,
        )
        assert resp.status_code == 403

    def test_update_not_found(self, test_client: TestClient, admin_headers: dict):
        resp = test_client.put(
            "/api/vehicles/99999",
            json={"price": 26000},
            headers=admin_headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
class TestDeleteVehicle:
    def _seed(self, client: TestClient, headers: dict) -> int:
        resp = client.post("/api/vehicles", json=VEHICLE_PAYLOAD, headers=headers)
        return resp.json()["id"]

    def test_delete_as_admin(self, test_client: TestClient, admin_headers: dict):
        vid = self._seed(test_client, admin_headers)
        resp = test_client.delete(f"/api/vehicles/{vid}", headers=admin_headers)
        assert resp.status_code == 204

    def test_delete_as_user(self, test_client: TestClient, admin_headers: dict, user_headers: dict):
        vid = self._seed(test_client, admin_headers)
        resp = test_client.delete(f"/api/vehicles/{vid}", headers=user_headers)
        assert resp.status_code == 403

    def test_delete_not_found(self, test_client: TestClient, admin_headers: dict):
        resp = test_client.delete("/api/vehicles/99999", headers=admin_headers)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PURCHASE
# ---------------------------------------------------------------------------
class TestPurchaseVehicle:
    def _seed(self, client: TestClient, headers: dict, quantity=10) -> int:
        resp = client.post(
            "/api/vehicles",
            json={**VEHICLE_PAYLOAD, "quantity": quantity},
            headers=headers,
        )
        return resp.json()["id"]

    def test_purchase_success(self, test_client: TestClient, admin_headers: dict, user_headers: dict):
        vid = self._seed(test_client, admin_headers, quantity=5)
        resp = test_client.post(f"/api/vehicles/{vid}/purchase", headers=user_headers)
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 4

    def test_purchase_out_of_stock(
        self, test_client: TestClient, admin_headers: dict, user_headers: dict
    ):
        vid = self._seed(test_client, admin_headers, quantity=0)
        resp = test_client.post(f"/api/vehicles/{vid}/purchase", headers=user_headers)
        assert resp.status_code == 400

    def test_purchase_not_found(
        self, test_client: TestClient, user_headers: dict
    ):
        resp = test_client.post("/api/vehicles/99999/purchase", headers=user_headers)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# RESTOCK
# ---------------------------------------------------------------------------
class TestRestockVehicle:
    def _seed(self, client: TestClient, headers: dict, quantity=5) -> int:
        resp = client.post(
            "/api/vehicles",
            json={**VEHICLE_PAYLOAD, "quantity": quantity},
            headers=headers,
        )
        return resp.json()["id"]

    def test_restock_as_admin(
        self, test_client: TestClient, admin_headers: dict
    ):
        vid = self._seed(test_client, admin_headers, quantity=5)
        resp = test_client.post(
            f"/api/vehicles/{vid}/restock",
            json={"quantity": 3},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["quantity"] == 8

    def test_restock_as_user(
        self, test_client: TestClient, admin_headers: dict, user_headers: dict
    ):
        vid = self._seed(test_client, admin_headers)
        resp = test_client.post(
            f"/api/vehicles/{vid}/restock",
            json={"quantity": 3},
            headers=user_headers,
        )
        assert resp.status_code == 403

    def test_restock_not_found(
        self, test_client: TestClient, admin_headers: dict
    ):
        resp = test_client.post(
            "/api/vehicles/99999/restock",
            json={"quantity": 3},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_restock_invalid_quantity(
        self, test_client: TestClient, admin_headers: dict
    ):
        vid = self._seed(test_client, admin_headers)
        resp = test_client.post(
            f"/api/vehicles/{vid}/restock",
            json={"quantity": 0},
            headers=admin_headers,
        )
        assert resp.status_code == 422
