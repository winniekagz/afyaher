"""Typesense adapter for curated passage indexing and topic-filtered search."""

from collections.abc import Mapping
from datetime import UTC, date, datetime, time
from hashlib import sha256
from typing import Any, Protocol

import typesense
from typesense.exceptions import (
    ObjectAlreadyExists,
    ObjectNotFound,
    TypesenseClientError,
)

from app.core.config import Settings
from app.schemas.educational import Topic
from app.schemas.knowledge import (
    CuratedPassage,
    KnowledgeSource,
    PassageReviewStatus,
)
from app.services.knowledge import is_eligible_for_production_retrieval
from app.services.typesense_schema import collection_schema


class TypesenseUnavailable(RuntimeError):
    """Raised for missing configuration or an unavailable Typesense service."""


class InvalidIndexedPassage(RuntimeError):
    """Raised when Typesense returns a malformed or ineligible passage."""


class TypesenseSchemaMismatch(RuntimeError):
    """Raised when an existing versioned collection does not match its schema."""


class SearchStore(Protocol):
    async def search(
        self, query: str, topic: Topic, limit: int
    ) -> list[tuple[dict[str, Any], int]]: ...


def create_typesense_client(settings: Settings) -> typesense.AsyncClient:
    if not settings.typesense_api_key.strip():
        raise TypesenseUnavailable("Typesense is not configured")
    try:
        return typesense.AsyncClient(
            {
                "api_key": settings.typesense_api_key,
                "nodes": [
                    {
                        "host": settings.typesense_host,
                        "port": str(settings.typesense_port),
                        "protocol": settings.typesense_protocol,
                    }
                ],
                "connection_timeout_seconds": settings.typesense_timeout_seconds,
                "num_retries": 0,
            }
        )
    except (TypeError, ValueError) as exc:
        raise TypesenseUnavailable("Typesense is not configured") from exc


def passage_content_hash(passage: str) -> str:
    return sha256(passage.encode("utf-8")).hexdigest()


def passage_document_id(record: CuratedPassage) -> str:
    content = "\0".join(
        (
            record.source_id,
            record.topic.value,
            record.section,
            passage_content_hash(record.passage),
        )
    )
    return f"{record.source_id}-p-{sha256(content.encode('utf-8')).hexdigest()[:24]}"


def _epoch(value: date | datetime) -> int:
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, time.min, tzinfo=UTC)
    return int(value.timestamp())


class TypesenseKnowledgeStore:
    def __init__(self, client: typesense.AsyncClient, collection: str):
        self.client = client
        self.collection = collection

    async def ensure_collection(self) -> bool:
        """Create the versioned collection if absent; return whether it was created."""
        try:
            existing = await self.client.collections[self.collection].retrieve()
            self._verify_collection_schema(existing)
            return False
        except ObjectNotFound:
            try:
                await self.client.collections.create(collection_schema(self.collection))
                return True
            except ObjectAlreadyExists:
                existing = await self.client.collections[self.collection].retrieve()
                self._verify_collection_schema(existing)
                return False
            except TypesenseClientError as exc:
                raise TypesenseUnavailable("Typesense is unavailable") from exc
        except TypesenseClientError as exc:
            raise TypesenseUnavailable("Typesense is unavailable") from exc

    def _verify_collection_schema(self, existing: Mapping[str, Any]) -> None:
        expected = collection_schema(self.collection)
        if not isinstance(existing, Mapping) or not isinstance(
            existing.get("fields"), list
        ):
            raise TypesenseSchemaMismatch("Collection schema is unreadable")
        actual_fields = {
            field.get("name"): field
            for field in existing["fields"]
            if isinstance(field, Mapping) and isinstance(field.get("name"), str)
        }
        for expected_field in expected["fields"]:
            actual = actual_fields.get(expected_field["name"])
            if actual is None or any(
                actual.get(
                    key, False if key in {"facet", "index", "optional"} else None
                )
                != value
                for key, value in expected_field.items()
                if key != "name"
            ):
                raise TypesenseSchemaMismatch(
                    "Existing collection does not match the versioned schema"
                )
        if existing.get("default_sorting_field") != expected["default_sorting_field"]:
            raise TypesenseSchemaMismatch(
                "Existing collection does not match the versioned schema"
            )

    async def upsert(self, document: dict[str, Any]) -> None:
        try:
            await self.client.collections[self.collection].documents.upsert(document)
        except TypesenseClientError as exc:
            raise TypesenseUnavailable("Typesense is unavailable") from exc

    async def prune_unapproved(self, approved_ids: set[str]) -> int:
        """Remove collection records no longer backed by approved local records."""
        try:
            document_ids: list[str] = []
            page = 1
            while True:
                result = await self.client.collections[
                    self.collection
                ].documents.search(
                    {
                        "q": "*",
                        "query_by": "passage",
                        "filter_by": "approval_status:=approved",
                        "per_page": 250,
                        "page": page,
                        "include_fields": "id",
                    }
                )
                if (
                    not isinstance(result, Mapping)
                    or not isinstance(result.get("hits"), list)
                    or type(result.get("found")) is not int
                ):
                    raise InvalidIndexedPassage("Malformed Typesense response")
                hits = result["hits"]
                for hit in hits:
                    document = hit.get("document") if isinstance(hit, Mapping) else None
                    document_id = (
                        document.get("id") if isinstance(document, Mapping) else None
                    )
                    if not isinstance(document_id, str):
                        raise InvalidIndexedPassage("Malformed Typesense hit")
                    document_ids.append(document_id)
                if page * 250 >= result["found"] or not hits:
                    break
                page += 1

            stale_ids = [
                doc_id for doc_id in document_ids if doc_id not in approved_ids
            ]
            for doc_id in stale_ids:
                await (
                    self.client.collections[self.collection].documents[doc_id].delete()
                )
            return len(stale_ids)
        except TypesenseClientError as exc:
            raise TypesenseUnavailable("Typesense is unavailable") from exc

    async def search(
        self, query: str, topic: Topic, limit: int
    ) -> list[tuple[dict[str, Any], int]]:
        try:
            result = await self.client.collections[self.collection].documents.search(
                {
                    "q": query,
                    "query_by": "passage",
                    "filter_by": (
                        f"topic:={topic.value} && approval_status:="
                        f"{PassageReviewStatus.APPROVED.value}"
                    ),
                    "per_page": limit,
                    "include_fields": (
                        "id,topic,source_id,source_title,source_url,section,passage,"
                        "publication_date,approved_at,approval_status,content_hash"
                    ),
                }
            )
        except TypesenseClientError as exc:
            raise TypesenseUnavailable("Typesense is unavailable") from exc

        if not isinstance(result, Mapping) or not isinstance(result.get("hits"), list):
            raise InvalidIndexedPassage("Malformed Typesense response")
        hits: list[tuple[dict[str, Any], int]] = []
        for hit in result["hits"]:
            if not isinstance(hit, Mapping):
                raise InvalidIndexedPassage("Malformed Typesense hit")
            document = hit.get("document")
            score = hit.get("text_match")
            if not isinstance(document, dict) or type(score) is not int:
                raise InvalidIndexedPassage("Malformed Typesense hit")
            hits.append((document, score))
        return hits


def make_index_document(
    record: CuratedPassage, source: KnowledgeSource
) -> dict[str, Any]:
    if record.review_status is not PassageReviewStatus.APPROVED:
        raise ValueError("Passage is not approved")
    if record.source_id != source.id or record.topic is not source.topic:
        raise ValueError("Passage source metadata does not match registry")
    if not is_eligible_for_production_retrieval(source):
        raise ValueError("Source is not eligible for production retrieval")
    assert record.approved_at is not None
    document: dict[str, Any] = {
        "id": passage_document_id(record),
        "topic": record.topic.value,
        "source_id": source.id,
        "source_title": source.title,
        "source_url": str(source.url),
        "section": record.section,
        "passage": record.passage,
        "approved_at": _epoch(record.approved_at),
        "approval_status": record.review_status.value,
        "content_hash": passage_content_hash(record.passage),
    }
    if record.publication_date is not None:
        document["publication_date"] = _epoch(record.publication_date)
    return document


def validate_search_hit(
    document: dict[str, Any],
    score: int,
    sources: Mapping[str, KnowledgeSource],
    topic: Topic,
    approved_passages: Mapping[str, CuratedPassage],
) -> dict[str, Any]:
    """Check indexed provenance again before returning any passage to a caller."""
    required = {
        "id",
        "topic",
        "source_id",
        "source_title",
        "source_url",
        "section",
        "passage",
        "approved_at",
        "approval_status",
        "content_hash",
    }
    if not required.issubset(document):
        raise InvalidIndexedPassage("Incomplete indexed passage")
    if type(document.get("approved_at")) is not int:
        raise InvalidIndexedPassage("Invalid approval timestamp")
    if "publication_date" in document and type(document["publication_date"]) is not int:
        raise InvalidIndexedPassage("Invalid publication date")
    source_id = document.get("source_id")
    source = sources.get(source_id) if isinstance(source_id, str) else None
    approved = document.get("id")
    approved_passage = (
        approved_passages.get(approved) if isinstance(approved, str) else None
    )
    passage = document.get("passage")
    section = document.get("section")
    if (
        source is None
        or approved_passage is None
        or not is_eligible_for_production_retrieval(source)
        or document.get("topic") != topic.value
        or source.topic is not topic
        or approved_passage.source_id != source.id
        or approved_passage.topic is not topic
        or approved_passage.review_status is not PassageReviewStatus.APPROVED
        or approved_passage.section != section
        or approved_passage.passage != passage
        or document.get("approved_at") != _epoch(approved_passage.approved_at)
        or document.get("publication_date")
        != (
            _epoch(approved_passage.publication_date)
            if approved_passage.publication_date is not None
            else None
        )
        or document.get("source_title") != source.title
        or document.get("source_url") != str(source.url)
        or document.get("approval_status") != PassageReviewStatus.APPROVED.value
        or not isinstance(passage, str)
        or not isinstance(section, str)
        or document.get("content_hash") != passage_content_hash(passage)
    ):
        raise InvalidIndexedPassage("Indexed passage failed provenance validation")
    if document.get("id") != passage_document_id(approved_passage):
        raise InvalidIndexedPassage("Indexed passage ID is inconsistent")
    return {
        "id": document["id"],
        "source_id": source.id,
        "source_title": source.title,
        "source_url": str(source.url),
        "topic": topic.value,
        "section": section,
        "passage": passage,
        "publication_date": document.get("publication_date"),
        "score": score,
        "content_hash": document["content_hash"],
    }
