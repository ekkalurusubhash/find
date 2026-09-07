import os

os.environ["ADMIN_API_KEY"] = "test-admin-key"

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_location() -> None:
    created = client.post("/api/locations", json={"latitude": 12.34, "longitude": 56.78})
    assert created.status_code == 201
    assert created.json()["latitude"] == 12.34

    listed = client.get("/api/locations", headers={"X-Admin-Key": "test-admin-key"})
    assert listed.status_code == 200
    assert listed.json()[0]["longitude"] == 56.78


def test_list_requires_admin_key() -> None:
    response = client.get("/api/locations")
    assert response.status_code == 401
