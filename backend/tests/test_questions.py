"""Private, synthetic Flow 01 scenarios; no real approvals or provider calls."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app
from app.schemas.educational import EducationalRequest, Topic
from app.schemas.knowledge import KnowledgeSource
from app.schemas.questions import QuestionResponse
from app.services import questions
from app.services.knowledge import is_eligible_for_production_retrieval
from app.services.knowledge_search import load_approved_material
from app.services.question_safety import screen_question
from app.services.typesense_store import (
    TypesenseUnavailable,
    make_index_document,
    passage_document_id,
)
from tests.test_knowledge import ELIGIBLE, make_source
from tests.test_typesense_knowledge import curated

ENDPOINT = "/api/v1/questions"


@pytest.fixture
def client():
    with TestClient(create_app(Settings(_env_file=None))) as client:
        yield client


@pytest.mark.parametrize(
    ("topic", "question", "expected"),
    [
        (
            "ovarian-torsion",
            "What is ovarian torsion, and why does it sometimes require surgery?",
            "insufficient_evidence",
        ),
        ("pcos", "Does PCOS always mean infertility?", "insufficient_evidence"),
        (
            "pcos",
            "What is the difference between an ovarian cyst and PCOS?",
            "insufficient_evidence",
        ),
        (
            "ovarian-torsion",
            "I suddenly have severe pelvic pain and I'm vomiting. What should I do?",
            "urgent_guidance",
        ),
        ("pcos", "I have one ovary. Do I need hormone supplements?", "out_of_scope"),
        ("pcos", "What is diabetes?", "out_of_scope"),
        ("pcos", "What is ovarian torsion?", "clarification_needed"),
        ("pcos", "Could you explain that more?", "clarification_needed"),
    ],
)
def test_representative_question_outcomes(client, topic, question, expected):
    response = client.post(ENDPOINT, json={"topic": topic, "question": question})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["status"] == expected
    assert body["citations"] == body["key_points"] == []
    assert body["grounding"] == "not_established"
    assert "question" not in body
    assert body["uncertainties"] and body["next_steps"]
    QuestionResponse.model_validate(body)


def test_urgent_and_scope_outcomes_do_not_touch_retrieval(client, monkeypatch):
    def forbidden(*_):
        pytest.fail("Safety interruption must precede retrieval/configuration")

    monkeypatch.setattr(questions, "load_approved_material", forbidden)
    monkeypatch.setattr(questions, "create_typesense_client", forbidden)
    urgent = client.post(
        ENDPOINT,
        json={"topic": "pcos", "question": "Sudden pelvic pain with vomiting."},
    ).json()
    assert urgent["status"] == "urgent_guidance"
    assert "Seek emergency care now" in urgent["short_answer"]
    assert urgent["suggested_clinician_questions"] == []
    unsupported = client.post(
        ENDPOINT, json={"topic": "pcos", "question": "Which medication should I take?"}
    ).json()
    assert unsupported["status"] == "out_of_scope"


@pytest.mark.parametrize(
    "text",
    [
        "Severe abdominal pain.",
        "Suddenly my tummy hurts and I feel sick.",
        "Pelvic pain and nausea.",
        "I suspect ovarian torsion.",
        "Ｓｕｄｄｅｎ pelvic pain.",
    ],
)
def test_conservative_urgent_rules(text):
    assert (
        screen_question(EducationalRequest(topic="pcos", question=text))
        == "urgent_notice"
    )


def test_empty_corpus_needs_no_network_or_key(client, monkeypatch):
    def forbidden(*_):
        pytest.fail("Empty approved corpus should abstain without a connection")

    monkeypatch.setattr(questions, "create_typesense_client", forbidden)
    assert (
        client.post(
            ENDPOINT, json={"topic": "pcos", "question": "What is PCOS?"}
        ).json()["reason"]
        == "no_approved_evidence"
    )


def fixture_material():
    # Fictional approval metadata confined to this test, never the real corpus.
    source = KnowledgeSource.model_validate(make_source(**ELIGIBLE))
    passage = curated().model_copy(update={"source_id": source.id})
    return {source.id: source}, {passage_document_id(passage): passage}


@pytest.mark.parametrize(
    "mode", ["no_results", "valid_candidate", "unavailable", "tampered"]
)
def test_retrieval_and_claim_gate_fail_closed(client, monkeypatch, mode):
    sources, approved = fixture_material()
    passage = next(iter(approved.values()))
    source = next(iter(sources.values()))
    monkeypatch.setattr(
        questions, "load_approved_material", lambda *_: (sources, approved)
    )
    fake_client = MagicMock()
    fake_client.api_call.aclose = AsyncMock()
    monkeypatch.setattr(questions, "create_typesense_client", lambda _: fake_client)

    class Store:
        def __init__(self, *_):
            pass

        async def search(self, query, topic, limit):
            assert topic is Topic.PCOS
            if mode == "unavailable":
                raise TypesenseUnavailable("private host credential details")
            if mode == "no_results":
                return []
            document = make_index_document(passage, source)
            if mode == "tampered":
                document["passage"] = "An invented unsupported medical claim."
            return [(document, 12)]

    monkeypatch.setattr(questions, "TypesenseKnowledgeStore", Store)
    response = client.post(
        ENDPOINT, json={"topic": "pcos", "question": "What is PCOS?"}
    )
    body = response.json()
    assert body["citations"] == body["key_points"] == []
    assert "private host" not in response.text
    assert "invented" not in response.text
    if mode in {"unavailable", "tampered"}:
        assert response.status_code == 503
        assert body["reason"] == "retrieval_unavailable"
    else:
        assert response.status_code == 200
        assert body["reason"] == (
            "verification_unavailable"
            if mode == "valid_candidate"
            else "no_approved_evidence"
        )
    fake_client.api_call.aclose.assert_awaited_once()


def test_unreadable_manifest_fails_safely(client, monkeypatch):
    def fail(*_):
        raise OSError("private filesystem details")

    monkeypatch.setattr(questions, "load_approved_material", fail)
    response = client.post(
        ENDPOINT, json={"topic": "pcos", "question": "What is PCOS?"}
    )
    assert response.status_code == 503
    assert "private filesystem" not in response.text


def test_metadata_only_cannot_be_retrieved_even_with_source_permission(tmp_path):
    source = make_source(**(ELIGIBLE | {"ingestion_status": "metadata_only"}))
    assert not is_eligible_for_production_retrieval(
        KnowledgeSource.model_validate(source)
    )
    registry = tmp_path / "registries"
    registry.mkdir()
    (registry / "pcos.json").write_text(
        json.dumps({"topic": "pcos", "sources": [source]})
    )
    passage = curated().model_copy(update={"source_id": source["id"]})
    manifest = tmp_path / "passages.json"
    manifest.write_text(json.dumps({"passages": [passage.model_dump(mode="json")]}))
    _, approved = load_approved_material(registry, manifest)
    assert approved == {}


def test_generated_answers_and_even_valid_but_unsupported_citations_are_blocked():
    request = EducationalRequest(topic="pcos", question="What is PCOS?")
    response = asyncio.run(questions.answer_question(request, Settings(_env_file=None)))
    data = response.model_dump()
    for changes in [
        {"status": "answered", "short_answer": "Invented claim"},
        {"key_points": ["Invented claim"]},
        {
            "citations": [
                {
                    "id": "invented",
                    "title": "Fake",
                    "publisher": "Fixture",
                    "url": "https://example.org",
                }
            ]
        },
        {
            "citations": [
                {
                    "id": "example-source",
                    "title": "Real fixture ID, unrelated to claim",
                    "publisher": "Fixture",
                    "url": "https://example.org",
                }
            ]
        },
    ]:
        with pytest.raises(ValidationError):
            QuestionResponse.model_validate(data | changes)


def test_invalid_input_does_not_echo_sensitive_fields(client):
    marker = "fictional-private-marker"
    response = client.post(
        ENDPOINT, json={"topic": marker, "question": marker, marker: True}
    )
    assert response.status_code == 422
    assert marker not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_body_limit_and_rate_limit(client):
    oversized = client.post(ENDPOINT, content=b"x" * 16_385)
    assert oversized.status_code == 413
    for _ in range(11):
        assert (
            client.post(
                ENDPOINT, json={"topic": "pcos", "question": "What is PCOS?"}
            ).status_code
            == 200
        )
    response = client.post(
        ENDPOINT, json={"topic": "pcos", "question": "What is PCOS?"}
    )
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
    assert response.headers["cache-control"] == "no-store"
