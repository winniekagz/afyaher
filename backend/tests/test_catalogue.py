"""Metadata boundary tests: no medical passage content or model requests."""

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import knowledge
from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app(Settings(_env_file=None, cors_origins=[]))) as client:
        yield client


def test_pcos_returns_only_catalogue_metadata(client):
    response = client.get("/api/v1/knowledge/sources?topic=pcos")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    data = response.json()
    assert data["topic"] == "pcos"
    assert {s["id"] for s in data["sources"]} == {
        "who-pcos",
        "fda-pcos",
        "monash-pcos-guideline",
    }
    for source in data["sources"]:
        assert set(source) == {
            "id",
            "topic",
            "title",
            "publisher",
            "url",
            "clinical_review_status",
            "ingestion_permission",
            "ingestion_status",
            "content_scope",
        }
        assert source["clinical_review_status"] == "not_reviewed"
        assert source["ingestion_permission"] == "not_verified"
        assert source["ingestion_status"] == "metadata_only"


@pytest.mark.parametrize("topic", ["ovarian-cysts", "ovarian-torsion"])
def test_unpopulated_topic_is_empty(client, topic):
    assert client.get(f"/api/v1/knowledge/sources?topic={topic}").json() == {
        "topic": topic,
        "sources": [],
    }


@pytest.mark.parametrize("query", ["", "?topic=unknown", "?topic=../../secret"])
def test_missing_or_unsupported_topic_rejected(client, query):
    assert client.get(f"/api/v1/knowledge/sources{query}").status_code == 422


def test_registry_failure_is_generic(client, monkeypatch):
    def fail(_):
        raise OSError("private filesystem details")

    monkeypatch.setattr(knowledge, "load_registry", fail)
    response = client.get("/api/v1/knowledge/sources?topic=pcos")
    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"detail": "Source catalogue unavailable"}
