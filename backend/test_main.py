import os

os.environ["ADMIN_API_KEY"] = "test-admin-key"

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Location API"


def test_local_origin_preflight_is_allowed() -> None:
    response = client.options(
        "/api/locations",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4200"


def test_delete_preflight_is_allowed() -> None:
    response = client.options(
        "/api/locations/1",
        headers={
            "Origin": "https://ekkalurusubhash.github.io",
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "x-admin-key",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://ekkalurusubhash.github.io"


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


def test_delete_location_requires_admin_key_and_removes_record() -> None:
    created = client.post("/api/locations", json={"latitude": 1.23, "longitude": 4.56})
    location_id = created.json()["id"]

    unauthorized = client.delete(f"/api/locations/{location_id}")
    assert unauthorized.status_code == 401

    deleted = client.delete(
        f"/api/locations/{location_id}",
        headers={"X-Admin-Key": "test-admin-key"},
    )
    assert deleted.status_code == 204

    listed = client.get("/api/locations", headers={"X-Admin-Key": "test-admin-key"})
    assert all(location["id"] != location_id for location in listed.json())


def test_headlines_are_public(monkeypatch) -> None:
    monkeypatch.setenv(
        "HEADLINES_JSON",
        '[{"title":"A new story","source":"Local desk","url":"https://example.com/story",'
        '"published_at":"2026-09-07T10:00:00+00:00"}]',
    )

    response = client.get("/api/headlines")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "A new story"
