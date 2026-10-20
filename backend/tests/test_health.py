import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app
from app.schemas.health import HealthResponse


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    with TestClient(create_app(Settings(_env_file=None))) as client:
        yield client


def test_health_contract(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "afyaher-api"}
    assert response.headers["content-type"] == "application/json"
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "origin, allowed",
    [
        ("http://127.0.0.1:3000", True),
        ("http://localhost:3000", True),
        ("http://127.0.0.1:3001", True),
        ("http://localhost:3001", True),
        ("https://untrusted.invalid", False),
        ("http://127.0.0.1:3002", False),
    ],
)
def test_cors_origin_allowlist(client, origin, allowed):
    response = client.get("/api/v1/health", headers={"Origin": origin})
    if allowed:
        assert response.headers["access-control-allow-origin"] == origin
    else:
        assert "access-control-allow-origin" not in response.headers


def test_disallowed_preflight(client):
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://untrusted.invalid",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_health_rejects_post(client):
    assert client.post("/api/v1/health").status_code == 405


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "ready", "service": "afyaher-api"},
        {"status": "ok", "service": "another-service"},
        {"status": "ok", "service": "afyaher-api", "secret": "synthetic"},
    ],
)
def test_health_schema_rejects_invalid_output(payload):
    with pytest.raises(ValidationError):
        HealthResponse.model_validate(payload)
