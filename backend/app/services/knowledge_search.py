"""Conservative retrieval orchestration; search results are candidates only."""

from collections.abc import Mapping
from typing import Any

from app.schemas.educational import Topic
from app.schemas.knowledge import CuratedPassage, KnowledgeSource
from app.schemas.retrieval import (
    EvidenceSufficiency,
    KnowledgeSearchHit,
    KnowledgeSearchResponse,
    RetrievalStatus,
)
from app.services.typesense_store import SearchStore, validate_search_hit


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
