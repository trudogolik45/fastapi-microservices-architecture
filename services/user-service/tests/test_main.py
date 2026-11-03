from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_liveness_probe_reports_alive():
    response = client.get("/health/liveness")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_purchases_endpoint_requires_token():
    response = client.get("/users/1/purchases/1")

    assert response.status_code in (401, 403)
