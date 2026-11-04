"""Source registry loading and content-use policies.

Three separate questions, each answered by one function:

- ``is_eligible_for_ingestion``: may this real source's content be processed
  (legal permission, recorded authorization, approved clinical review)?
- ``can_chunk``: may we split this source's text into passages? Allows
  eligible sources and explicit development-only synthetic fixtures.
- ``is_eligible_for_production_retrieval``: may passages from this source
  support answers or citations shown to users? Never true for synthetic
  fixtures, whatever their other fields say.

Nothing here scrapes, downloads, embeds, or stores medical content.
"""

from pathlib import Path

from app.schemas.knowledge import (
    ClinicalReviewStatus,
    ContentScope,
    EvidenceType,
    IngestionPermission,
    KnowledgeSource,
    SourceRegistry,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SOURCES_DIR = DATA_DIR / "sources"
SYNTHETIC_DIR = DATA_DIR / "fixtures" / "synthetic"


def load_registry(path: Path) -> SourceRegistry:
    """Read and validate a registry file.

    Raises OSError if the file cannot be read and pydantic.ValidationError
    if its JSON is malformed or fails schema validation.
    """
    return SourceRegistry.model_validate_json(path.read_text(encoding="utf-8"))


def is_eligible_for_ingestion(source: KnowledgeSource) -> bool:
    """Return True only when legal permission and clinical review are both explicit.

    Unknown permission (``not_verified``) is never eligible.
    """
    return (
        source.ingestion_permission is IngestionPermission.PERMITTED
        and source.license is not None
        and source.authorization_reference is not None
        and source.authorization_date is not None
        and source.clinical_review_status is ClinicalReviewStatus.APPROVED
    )


def is_synthetic_fixture(source: KnowledgeSource) -> bool:
    return source.evidence_type is EvidenceType.SYNTHETIC_FIXTURE


def can_chunk(source: KnowledgeSource) -> bool:
    """Return True if the source's text may be split into passages."""
    if is_synthetic_fixture(source):
        return source.content_scope is ContentScope.DEVELOPMENT_ONLY
    return is_eligible_for_ingestion(source)


def is_eligible_for_production_retrieval(source: KnowledgeSource) -> bool:
    """Return True only for eligible, production-scoped, non-synthetic sources."""
    return (
        not is_synthetic_fixture(source)
        and source.content_scope is ContentScope.PRODUCTION
        and is_eligible_for_ingestion(source)
    )
