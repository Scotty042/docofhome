from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_unknown_api_route_returns_json_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")


def test_path_traversal_is_not_served() -> None:
    with TestClient(app) as client:
        response = client.get("/../../etc/passwd")
    assert response.status_code in {404, 503}
    assert "root:" not in response.text
