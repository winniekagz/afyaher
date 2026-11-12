"""Typesense adapter, approval gate and retrieval-abstention tests.

Only synthetic source metadata and fictional, non-medical passages are used.
"""

import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from pydantic import ValidationError
from typesense.exceptions import ObjectNotFound

from app.api.v1 import knowledge as knowledge_api
from app.core.config import Settings
from app.main import create_app
from app.schemas.educational import Topic
from app.schemas.knowledge import (
    CuratedPassage,
    KnowledgeSource,
    PassageReviewStatus,
)
from app.schemas.retrieval import EvidenceSufficiency, RetrievalStatus
from app.services.knowledge_search import search_approved_knowledge
from app.services.typesense_schema import collection_schema
from app.services.typesense_store import (
    InvalidIndexedPassage,
    TypesenseKnowledgeStore,
    make_index_document,
    passage_content_hash,
    passage_document_id,
    validate_search_hit,
)
from scripts import index_approved_passages as indexing
from tests.test_knowledge import ELIGIBLE, make_source

APPROVED_AT = datetime(2026, 11, 10, 9, 0, tzinfo=UTC)
FICTIONAL_PASSAGE = "Copper kettles hum at noon in a fictional archive."


def eligible_source(topic: str = "pcos") -> KnowledgeSource:
    return KnowledgeSource.model_validate(
        make_source(id="example-source", topic=topic, **ELIGIBLE)
    )


def curated(
    status: PassageReviewStatus = PassageReviewStatus.APPROVED,
    topic: Topic = Topic.PCOS,
) -> CuratedPassage:
    approved = status is PassageReviewStatus.APPROVED
    return CuratedPassage(
        source_id="example-source",
        topic=topic,
        section="Fictional section",
        passage=FICTIONAL_PASSAGE,
        review_status=status,
        approved_at=APPROVED_AT if approved else None,
        reviewer_qualification="Synthetic fixture reviewer" if approved else None,
    )


def test_collection_schema_is_versioned_and_topic_filterable():
    schema = collection_schema("afyaher_knowledge_v2")
    fields = {field["name"]: field for field in schema["fields"]}
    assert schema["name"].endswith("_v2")
    assert fields["topic"]["facet"] is True
    assert fields["passage"]["type"] == "string"
    assert fields["source_id"]["facet"] is True
    assert fields["approved_at"]["type"] == "int64"


def test_deterministic_passage_id_and_hash():
    first = curated()
    assert passage_document_id(first) == passage_document_id(curated())
    assert passage_content_hash(first.passage) == passage_content_hash(
        FICTIONAL_PASSAGE
    )
    changed = first.model_copy(update={"passage": "A changed fictional passage."})
    assert passage_document_id(first) != passage_document_id(changed)


def test_pending_or_rejected_passage_cannot_be_indexed():
    for status in (PassageReviewStatus.PENDING_REVIEW, PassageReviewStatus.REJECTED):
        with pytest.raises(ValueError, match="not approved"):
            make_index_document(curated(status), eligible_source())


def test_source_registry_permission_is_required_for_indexing():
    unreviewed = KnowledgeSource.model_validate(make_source(id="example-source"))
    with pytest.raises(ValueError, match="not eligible"):
        make_index_document(curated(), unreviewed)


def test_index_document_keeps_traceable_metadata_and_content_hash():
    document = make_index_document(curated(), eligible_source())
    assert document["topic"] == "pcos"
    assert document["source_id"] == "example-source"
    assert document["source_title"] == "Example source"
    assert document["source_url"] == "https://example.org/pcos"
    assert document["approval_status"] == "approved"
    assert document["content_hash"] == passage_content_hash(FICTIONAL_PASSAGE)


def test_passage_review_record_requires_timezone_and_reviewer_qualification():
    data = curated().model_dump()
    data["approved_at"] = datetime(2026, 1, 1)
    with pytest.raises(ValidationError):
        CuratedPassage.model_validate(data)
    with pytest.raises(ValidationError):
        CuratedPassage(
            source_id="example-source",
            topic="pcos",
            section="Fictional section",
            passage=FICTIONAL_PASSAGE,
            review_status="approved",
            approved_at=APPROVED_AT,
        )


def test_typesense_collection_creation_and_existing_collection_handling():
    client = MagicMock()
    collection = MagicMock()
    client.collections.__getitem__.return_value = collection
    collection.retrieve = AsyncMock(
        return_value=collection_schema("afyaher_knowledge_v2")
    )
    client.collections.create = AsyncMock()
    store = TypesenseKnowledgeStore(client, "afyaher_knowledge_v2")
    assert asyncio.run(store.ensure_collection()) is False
    client.collections.create.assert_not_awaited()

    collection.retrieve = AsyncMock(side_effect=ObjectNotFound("not found"))
    client.collections.create = AsyncMock(return_value={"name": "afyaher_knowledge_v2"})
    assert asyncio.run(store.ensure_collection()) is True
    client.collections.create.assert_awaited_once_with(
        collection_schema("afyaher_knowledge_v2")
    )


class FakeStore:
    def __init__(self, results):
        self.results = results
        self.query = None

    async def search(self, query, topic, limit):
        self.query = (query, topic, limit)
        return self.results


def test_search_returns_candidates_but_never_claims_sufficiency():
    source = eligible_source()
    document = make_index_document(curated(), source)
    store = FakeStore([(document, 13)])
    result = asyncio.run(
        search_approved_knowledge(
            "copper archive",
            Topic.PCOS,
            {source.id: source},
            {document["id"]: curated()},
            store,
            4,
        )
    )
    assert result.status is RetrievalStatus.CANDIDATES_FOUND
    assert result.evidence_sufficiency is EvidenceSufficiency.NOT_ASSESSED
    assert str(result.passages[0].source_url) == "https://example.org/pcos"
    assert store.query == ("copper archive", Topic.PCOS, 4)


def test_empty_search_abstains():
    result = asyncio.run(
        search_approved_knowledge(
            "no fictional match", Topic.PCOS, {}, {}, FakeStore([])
        )
    )
    assert result.status is RetrievalStatus.NO_MATCHING_EVIDENCE
    assert result.evidence_sufficiency is EvidenceSufficiency.INSUFFICIENT
    assert result.passages == []


@pytest.mark.parametrize(
    "mutation",
    [
        {"topic": "ovarian-cysts"},
        {"approval_status": "pending_review"},
        {"source_title": "Unregistered title"},
        {"content_hash": "0" * 64},
        {"passage": "tampered text"},
    ],
)
def test_tampered_or_wrong_topic_hits_are_rejected(mutation):
    source = eligible_source()
    document = make_index_document(curated(), source) | mutation
    with pytest.raises(InvalidIndexedPassage):
        validate_search_hit(
            document,
            5,
            {source.id: source},
            Topic.PCOS,
            {document["id"]: curated()},
        )


def test_search_uses_topic_and_approval_filters():
    client = MagicMock()
    collection = MagicMock()
    client.collections.__getitem__.return_value = collection
    collection.documents.search = AsyncMock(return_value={"hits": []})
    store = TypesenseKnowledgeStore(client, "afyaher_knowledge_v2")
    result = asyncio.run(store.search("fiction", Topic.OVARIAN_TORSION, 3))
    assert result == []
    parameters = collection.documents.search.await_args.args[0]
    assert (
        parameters["filter_by"] == "topic:=ovarian-torsion && approval_status:=approved"
    )
    assert parameters["query_by"] == "passage"


def test_index_reconciliation_removes_records_without_current_approval():
    client = MagicMock()
    collection = MagicMock()
    client.collections.__getitem__.return_value = collection
    collection.documents.search = AsyncMock(
        return_value={
            "found": 2,
            "hits": [
                {"document": {"id": "retained"}},
                {"document": {"id": "revoked"}},
            ],
        }
    )
    collection.documents.__getitem__.return_value.delete = AsyncMock()
    store = TypesenseKnowledgeStore(client, "afyaher_knowledge_v2")
    assert asyncio.run(store.prune_unapproved({"retained"})) == 1
    collection.documents["revoked"].delete.assert_awaited_once()


def test_malformed_search_hits_raise_safe_validation_error():
    client = MagicMock()
    collection = MagicMock()
    client.collections.__getitem__.return_value = collection
    collection.documents.search = AsyncMock(return_value={"hits": [{"document": {}}]})
    store = TypesenseKnowledgeStore(client, "afyaher_knowledge_v2")
    with pytest.raises(InvalidIndexedPassage):
        asyncio.run(store.search("fiction", Topic.PCOS, 3))


def test_index_command_skips_pending_passages_and_upserts_approved(
    tmp_path, monkeypatch
):
    pending = curated(PassageReviewStatus.PENDING_REVIEW).model_dump(mode="json")
    approved = curated().model_dump(mode="json")
    passage_file = tmp_path / "passages.json"
    passage_file.write_text(json.dumps({"passages": [pending, approved]}))

    source = eligible_source()
    monkeypatch.setattr(indexing, "_load_sources", lambda: {source.id: source})
    client = MagicMock()
    client.api_call.aclose = AsyncMock()
    monkeypatch.setattr(indexing, "create_typesense_client", lambda _: client)

    class Store:
        def __init__(self, *_):
            self.upsert = AsyncMock()

        async def ensure_collection(self):
            return True

        async def prune_unapproved(self, approved_ids):
            return 0

    monkeypatch.setattr(indexing, "TypesenseKnowledgeStore", Store)
    report = asyncio.run(
        indexing.index_file(
            passage_file, Settings(_env_file=None, typesense_api_key="test")
        )
    )
    assert report["indexed"] == 1
    assert report["skipped"][0]["reason"] == "pending_review"


def test_search_api_returns_candidates_and_sufficiency_not_assessed(
    tmp_path, monkeypatch
):
    source = eligible_source()
    registry_path = tmp_path / "pcos.json"
    registry_path.write_text(
        json.dumps(
            {"topic": "pcos", "sources": [make_source(id="example-source", **ELIGIBLE)]}
        )
    )
    approved_dir = tmp_path / "approved"
    approved_dir.mkdir()
    approved_path = approved_dir / "passages.json"
    approved_path.write_text(
        json.dumps({"passages": [curated().model_dump(mode="json")]})
    )
    monkeypatch.setattr(knowledge_api, "SOURCES_DIR", tmp_path)
    monkeypatch.setattr(knowledge_api, "APPROVED_PASSAGES_FILE", approved_path)

    client = MagicMock()
    client.api_call.aclose = AsyncMock()
    monkeypatch.setattr(knowledge_api, "create_typesense_client", lambda _: client)

    class Store:
        def __init__(self, *_):
            pass

        async def search(self, _query, topic, _limit):
            assert topic is Topic.PCOS
            return [(make_index_document(curated(), source), 15)]

    monkeypatch.setattr(knowledge_api, "TypesenseKnowledgeStore", Store)

    async def post():
        transport = httpx.ASGITransport(app=create_app(Settings(_env_file=None)))
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post(
                "/api/v1/knowledge/search",
                json={"topic": "pcos", "question": "Fictional archive?"},
            )

    response = asyncio.run(post())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "candidates_found"
    assert body["evidence_sufficiency"] == "not_assessed"
    assert body["passages"][0]["source_id"] == "example-source"


def test_search_api_reports_safe_unavailable_response(monkeypatch):
    from app.services.typesense_store import TypesenseUnavailable

    def unavailable(_settings):
        raise TypesenseUnavailable("private host and key details")

    monkeypatch.setattr(knowledge_api, "create_typesense_client", unavailable)

    async def post():
        transport = httpx.ASGITransport(app=create_app(Settings(_env_file=None)))
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post(
                "/api/v1/knowledge/search",
                json={"topic": "pcos", "question": "Fictional archive?"},
            )

    response = asyncio.run(post())
    assert response.status_code == 503
    assert response.json()["status"] == "retrieval_unavailable"
    assert "private host" not in response.text


def test_search_request_uses_existing_question_validation():
    async def post():
        transport = httpx.ASGITransport(app=create_app(Settings(_env_file=None)))
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post(
                "/api/v1/knowledge/search",
                json={"topic": "pcos", "question": "ab"},
            )

    response = asyncio.run(post())
    assert response.status_code == 422
