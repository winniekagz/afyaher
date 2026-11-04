"""Map cited passage IDs to displayable source references.

Citation metadata (title, publisher, URL) always comes from the registry,
never from model output. A valid mapping proves only that a citation
refers to a real retrieved passage; it does not prove the passage
supports the claim.

Resolution always applies the production retrieval policy, so passages
from synthetic fixtures or non-production sources can never become
user-facing citations.
"""

from collections.abc import Iterable

from app.schemas.educational import SourceReference
from app.schemas.knowledge import SourcePassage, SourceRegistry
from app.services.knowledge import is_eligible_for_production_retrieval


class CitationError(ValueError):
    """Raised when a citation cannot be mapped to an eligible retrieved passage."""


def resolve_citations(
    cited_passage_ids: Iterable[str],
    retrieved: Iterable[SourcePassage],
    registry: SourceRegistry,
) -> list[SourceReference]:
    """Return unique source references in first-cited order.

    Raises CitationError if any cited ID was not retrieved, or if its
    source is missing from the registry or not eligible for production
    retrieval.
    """
    passages: dict[str, SourcePassage] = {}
    for passage in retrieved:
        if passage.id in passages:
            raise CitationError(f"Duplicate retrieved passage ID '{passage.id}'")
        passages[passage.id] = passage
    sources = {s.id: s for s in registry.sources}

    references: dict[str, SourceReference] = {}
    for passage_id in cited_passage_ids:
        passage = passages.get(passage_id)
        if passage is None:
            raise CitationError(f"Cited passage '{passage_id}' was not retrieved")
        source = sources.get(passage.source_id)
        if source is None:
            raise CitationError(
                f"Passage '{passage_id}' references unknown source "
                f"'{passage.source_id}'"
            )
        if not is_eligible_for_production_retrieval(source):
            raise CitationError(
                f"Passage '{passage_id}' comes from ineligible source '{source.id}' "
                "(not eligible for production retrieval)"
            )
        if (
            passage.topic is not source.topic
            or passage.id != f"{source.id}-p{passage.position}"
        ):
            raise CitationError(
                f"Passage '{passage_id}' has inconsistent source metadata"
            )
        if source.id not in references:
            references[source.id] = SourceReference(
                id=source.id,
                title=source.title,
                publisher=source.publisher,
                url=source.url,
            )
    return list(references.values())
