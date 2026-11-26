"""Conservative retrieval orchestration; search results are candidates only."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.schemas.educational import Topic
from app.schemas.knowledge import (
    CuratedPassage,
    CuratedPassageBatch,
    KnowledgeSource,
    PassageReviewStatus,
)
from app.schemas.retrieval import (
    EvidenceSufficiency,
    KnowledgeSearchHit,
    KnowledgeSearchResponse,
    RetrievalStatus,
)
from app.services.knowledge import is_eligible_for_production_retrieval, load_registry
from app.services.typesense_store import (
    SearchStore,
    passage_document_id,
    validate_search_hit,
)


def load_approved_material(
    sources_dir: Path, passage_file: Path
) -> tuple[dict[str, KnowledgeSource], dict[str, CuratedPassage]]:
    """Current approval snapshots, shared by search and the question flow."""
    sources: dict[str, KnowledgeSource] = {}
    for path in sorted(sources_dir.glob("*.json")):
        for source in load_registry(path).sources:
            if source.id in sources:
                raise ValueError("Duplicate source metadata")
            sources[source.id] = source
    batch = CuratedPassageBatch.model_validate_json(
        passage_file.read_text(encoding="utf-8")
    )
    approved: dict[str, CuratedPassage] = {}
    for passage in batch.passages:
        if passage.review_status is not PassageReviewStatus.APPROVED:
            continue
        source = sources.get(passage.source_id)
        if source is None or passage.topic is not source.topic:
            raise ValueError("Approved passage source is missing or inconsistent")
        if is_eligible_for_production_retrieval(source):
            passage_id = passage_document_id(passage)
            if passage_id in approved:
                raise ValueError("Duplicate approved passage")
            approved[passage_id] = passage
    return sources, approved


async def search_approved_knowledge(
    query: str,
    topic: Topic,
    sources: Mapping[str, KnowledgeSource],
    approved_passages: Mapping[str, CuratedPassage],
    store: SearchStore,
    limit: int = 5,
) -> KnowledgeSearchResponse:
    """Return traceable candidates or abstain; never infer claim support."""
    raw_hits = await store.search(query, topic, limit)
    if not raw_hits:
        return KnowledgeSearchResponse(
            status=RetrievalStatus.NO_MATCHING_EVIDENCE,
            topic=topic,
            evidence_sufficiency=EvidenceSufficiency.INSUFFICIENT,
            passages=[],
            reason="No matching approved passages were found for this topic.",
        )

    hits: list[KnowledgeSearchHit] = []
    for document, score in raw_hits:
        safe_hit: dict[str, Any] = validate_search_hit(
            document, score, sources, topic, approved_passages
        )
        hits.append(KnowledgeSearchHit.model_validate(safe_hit))
    return KnowledgeSearchResponse(
        status=RetrievalStatus.CANDIDATES_FOUND,
        topic=topic,
        evidence_sufficiency=EvidenceSufficiency.NOT_ASSESSED,
        passages=hits,
        reason=(
            "Retrieved passages are candidates only. Claim support has not been "
            "assessed, so no answer is generated from them."
        ),
    )
