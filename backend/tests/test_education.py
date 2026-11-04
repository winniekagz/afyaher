"""Tests for POST /api/v1/education/ask.

Covers: request validation (Pydantic schema), HTTP 422 rejection,
valid response contract, stub service_unavailable behavior, CORS
preflight for POST, and method restrictions.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app
from app.schemas.educational import (
    AnswerStatus,
    EducationalRequest,
    EducationalResponse,
    SourceReference,
)

ENDPOINT = "/api/v1/education/ask"
DISCLAIMER = (
    "This is educational information, not medical advice. "
    "Consult a qualified clinician for personal health decisions."
)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    with TestClient(create_app(Settings(_env_file=None))) as c:
        yield c


# ── Valid requests ────────────────────────────────────────────────


class TestValidRequests:
    """Valid payloads must return HTTP 200 with the expected contract."""

    def test_pcos_question(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "What is PCOS?"},
        )
        assert resp.status_code == 200

    def test_ovarian_cysts_question(self, client):
        resp = client.post(
            ENDPOINT,
            json={
                "topic": "ovarian-cysts",
                "question": "What is an ovarian cyst?",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["topic"] == "ovarian-cysts"

    def test_ovarian_torsion_question(self, client):
        resp = client.post(
            ENDPOINT,
            json={
                "topic": "ovarian-torsion",
                "question": "What is ovarian torsion?",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["topic"] == "ovarian-torsion"

    def test_leading_trailing_whitespace_normalised(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "  What is PCOS?  "},
        )
        assert resp.status_code == 200
        assert resp.json()["question"] == "What is PCOS?"

    def test_internal_whitespace_preserved(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "a b c"},
        )
        assert resp.status_code == 200
        assert resp.json()["question"] == "a b c"


# ── Invalid requests → HTTP 422 ──────────────────────────────────


class TestInvalidRequests:
    """Pydantic validation failures must surface as HTTP 422."""

    def test_empty_question(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": ""},
        )
        assert resp.status_code == 422

    def test_whitespace_only_question(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "     "},
        )
        assert resp.status_code == 422

    def test_fewer_than_three_non_whitespace(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "ab"},
        )
        assert resp.status_code == 422

    def test_question_exceeds_2000_characters(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "a" * 2001},
        )
        assert resp.status_code == 422

    def test_unsupported_topic(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "diabetes", "question": "What is this?"},
        )
        assert resp.status_code == 422

    def test_missing_topic(self, client):
        resp = client.post(
            ENDPOINT,
            json={"question": "What is PCOS?"},
        )
        assert resp.status_code == 422

    def test_non_string_question(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": 42},
        )
        assert resp.status_code == 422

    def test_unexpected_field_rejected(self, client):
        resp = client.post(
            ENDPOINT,
            json={
                "topic": "pcos",
                "question": "What is PCOS?",
                "exampleIndex": 0,
            },
        )
        assert resp.status_code == 422

    def test_no_body(self, client):
        resp = client.post(ENDPOINT)
        assert resp.status_code == 422


# ── Response contract ─────────────────────────────────────────────


class TestResponseContract:
    """The stub must return a well-formed EducationalResponse."""

    def test_full_response_shape(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "What is PCOS?"},
        )
        body = resp.json()
        assert body["status"] == "service_unavailable"
        assert body["topic"] == "pcos"
        assert body["question"] == "What is PCOS?"
        assert body["answer"] == "Educational answers are not available yet."
        assert body["sources"] == []
        assert isinstance(body["limitations"], str)
        assert len(body["limitations"]) > 0
        assert body["disclaimer"] == DISCLAIMER

    def test_content_type_json(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "What is PCOS?"},
        )
        assert resp.headers["content-type"] == "application/json"

    def test_response_validates_against_schema(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "What is PCOS?"},
        )
        parsed = EducationalResponse.model_validate(resp.json())
        assert parsed.status == AnswerStatus.SERVICE_UNAVAILABLE


# ── 422 error detail ─────────────────────────────────────────────


class TestErrorDetail:
    """422 responses must contain a structured detail array."""

    def test_detail_array_present(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": ""},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert isinstance(body["detail"], list)
        assert len(body["detail"]) >= 1
        assert "msg" in body["detail"][0]
        assert "type" in body["detail"][0]


# ── Method restrictions ───────────────────────────────────────────


class TestMethodRestrictions:
    def test_get_not_allowed(self, client):
        assert client.get(ENDPOINT).status_code == 405

    def test_put_not_allowed(self, client):
        resp = client.put(
            ENDPOINT,
            json={"topic": "pcos", "question": "What is PCOS?"},
        )
        assert resp.status_code == 405


# ── CORS for POST ─────────────────────────────────────────────────


class TestCorsPost:
    def test_allowed_origin(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "What is PCOS?"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert (
            resp.headers["access-control-allow-origin"]
            == "http://localhost:3000"
        )

    def test_disallowed_origin(self, client):
        resp = client.post(
            ENDPOINT,
            json={"topic": "pcos", "question": "What is PCOS?"},
            headers={"Origin": "https://untrusted.invalid"},
        )
        assert "access-control-allow-origin" not in resp.headers

    def test_preflight_options(self, client):
        resp = client.options(
            ENDPOINT,
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert resp.status_code == 200
        assert (
            resp.headers["access-control-allow-origin"]
            == "http://localhost:3000"
        )


# ── Schema-level validation (no HTTP) ────────────────────────────


class TestRequestSchemaValidation:
    """Direct Pydantic validation without the HTTP layer."""

    def test_tabs_and_newlines_rejected(self):
        with pytest.raises(ValidationError) as exc_info:
            EducationalRequest(topic="pcos", question="\t\n\r\n")
        assert any(
            "non-whitespace" in e["msg"]
            for e in exc_info.value.errors()
        )

    def test_three_non_whitespace_accepted(self):
        req = EducationalRequest(topic="pcos", question="abc")
        assert req.question == "abc"

    def test_two_non_whitespace_rejected(self):
        with pytest.raises(ValidationError):
            EducationalRequest(topic="pcos", question="ab")

    def test_unicode_preserved(self):
        req = EducationalRequest(topic="pcos", question="PCOS ni nini?")
        assert req.question == "PCOS ni nini?"

    def test_exactly_2000_characters_accepted(self):
        req = EducationalRequest(topic="pcos", question="a" * 2000)
        assert len(req.question) == 2000

    def test_non_string_list_rejected(self):
        with pytest.raises(ValidationError):
            EducationalRequest(topic="pcos", question=["What?"])


class TestAnswerStatusEnum:
    """AnswerStatus must include all documented application statuses."""

    def test_service_unavailable_member(self):
        assert AnswerStatus.SERVICE_UNAVAILABLE == "service_unavailable"

    def test_all_statuses(self):
        expected = {
            "answered",
            "insufficient_evidence",
            "clarification_needed",
            "out_of_scope",
            "urgent_guidance",
            "service_unavailable",
        }
        assert {s.value for s in AnswerStatus} == expected


class TestSourceReferenceUrlValidation:
    """SourceReference.url must reject invalid URLs."""

    def test_valid_https_url(self):
        ref = SourceReference(
            id="who-pcos",
            title="PCOS",
            publisher="WHO",
            url="https://www.who.int/pcos",
        )
        assert "who.int" in str(ref.url)

    def test_invalid_url_rejected(self):
        with pytest.raises(ValidationError):
            SourceReference(
                id="bad",
                title="Bad",
                publisher="None",
                url="not-a-url",
            )

    def test_url_serialises_as_string_in_json(self):
        ref = SourceReference(
            id="who-pcos",
            title="PCOS",
            publisher="WHO",
            url="https://www.who.int/pcos",
        )
        data = ref.model_dump(mode="json")
        assert isinstance(data["url"], str)
        assert data["url"] == "https://www.who.int/pcos"


class TestResponseSchemaValidation:
    """Direct EducationalResponse schema checks."""

    def test_response_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            EducationalResponse(
                status="answered",
                topic="pcos",
                question="What is PCOS?",
                answer="Answer text.",
                sources=[],
                secret="leaked",
            )

    def test_response_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            EducationalResponse(
                status="made_up",
                topic="pcos",
                question="What is PCOS?",
                answer="text",
                sources=[],
            )

    def test_service_unavailable_response_valid(self):
        resp = EducationalResponse(
            status="service_unavailable",
            topic="pcos",
            question="What is PCOS?",
            answer="Educational answers are not available yet.",
            sources=[],
            limitations="The evidence-backed answer service is not implemented.",
        )
        assert resp.disclaimer == DISCLAIMER
