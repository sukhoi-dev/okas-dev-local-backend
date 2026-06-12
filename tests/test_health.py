"""Tests for the /health endpoint — no DB dependency."""


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body(client):
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert data["service"] == "okas-cloud-backend"


def test_health_method_not_allowed(client):
    assert client.post("/health").status_code == 405


def test_unknown_route_returns_404(client):
    assert client.get("/this-does-not-exist").status_code == 404
