"""API documentation contracts; examples contain synthetic non-clinical text."""

import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from scripts.export_openapi import DEFAULT_OUTPUT
from scripts.export_openapi import main as export_main


@pytest.fixture
def client():
    with TestClient(create_app(Settings(_env_file=None, cors_origins=[]))) as client:
        yield client


def test_swagger_and_redoc_reference_live_openapi(client):
    for path in ("/docs", "/redoc"):
        response = client.get(path)
        assert response.status_code == 200
        assert "/openapi.json" in response.text


def test_checked_in_schema_matches_live_documentation(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == json.loads(DEFAULT_OUTPUT.read_text("utf-8"))
    assert set(response.json()["paths"]) == {
        "/api/v1/health",
        "/api/v1/education/ask",
        "/api/v1/knowledge/sources",
        "/api/v1/knowledge/search",
    }


def test_swagger_example_matches_actual_unavailable_response(client):
    operation = client.get("/openapi.json").json()["paths"]["/api/v1/education/ask"][
        "post"
    ]
    examples = operation["requestBody"]["content"]["application/json"]["examples"]
    expected = operation["responses"]["200"]["content"]["application/json"]["example"]
    for example in examples.values():
        response = client.post("/api/v1/education/ask", json=example["value"])
        assert response.status_code == 200
        assert response.json() == expected | example["value"]
    assert "422" in operation["responses"]
    assert "405" in operation["responses"]


def test_openapi_export_is_reproducible(tmp_path):
    output = tmp_path / "api" / "openapi.json"
    assert export_main(["--out", str(output)]) == 0
    assert output.read_bytes() == DEFAULT_OUTPUT.read_bytes()
