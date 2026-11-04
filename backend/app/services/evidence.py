"""Internal provenance checks; no outcome authorizes answer generation."""

from collections.abc import Iterable
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from app.schemas.educational import Topic
from app.schemas.knowledge import RetrievedPassage, SourcePassage, SourceRegistry
from app.services.citations import CitationError, resolve_citations


class EvidenceStatus(StrEnum):
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INVALID_EVIDENCE = "invalid_evidence"
    SUPPORT_ASSESSMENT_REQUIRED = "support_assessment_required"


class EvidenceResult(BaseModel):
    """Candidate provenance only, never clinical sufficiency or claim support."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: EvidenceStatus
    candidates: tuple[SourcePassage, ...] = ()

    @model_validator(mode="after")
    def check_candidates(self) -> "EvidenceResult":
        requires_support = self.status is EvidenceStatus.SUPPORT_ASSESSMENT_REQUIRED
        if bool(self.candidates) != requires_support:
            raise ValueError(
                "Only support_assessment_required must contain candidate passages"
            )
        return self


def assess_provenance(
    topic: Topic,
    retrieved: Iterable[RetrievedPassage],
    registry: SourceRegistry,
) -> EvidenceResult:
    """Check an entire retrieval batch against fixed production provenance rules.

    The registry is already validated by the caller. Revalidate retrieval
    records because Pydantic models can be mutated or copied without validation.
    Candidate snapshots preserve retrieval order, but omit ranking metadata.
    Positions need not be consecutive in a ranked retrieval subset.

    No logging, storage, question processing, or claim-support assessment occurs.
    Even a structurally valid batch still requires a separate support assessment.
    """
    passages: list[SourcePassage] = []
    invalid = False
    seen_record = False
    for record in retrieved:
        seen_record = True
        try:
            checked = RetrievedPassage.model_validate(
                record.model_dump(warnings=False), strict=True
            )
        except ValidationError:
            invalid = True
            continue
        passage = checked.passage
        if passage.topic != topic or registry.topic != topic:
            invalid = True
        passages.append(passage)

    if not seen_record:
        return EvidenceResult(status=EvidenceStatus.INSUFFICIENT_EVIDENCE)
    if invalid:
        return EvidenceResult(status=EvidenceStatus.INVALID_EVIDENCE)

    try:
        # Cite every candidate internally so none bypasses source eligibility or
        # ID/topic consistency checks. Discard the display-reference result.
        resolve_citations((p.id for p in passages), passages, registry)
    except CitationError:
        return EvidenceResult(status=EvidenceStatus.INVALID_EVIDENCE)

    return EvidenceResult(
        status=EvidenceStatus.SUPPORT_ASSESSMENT_REQUIRED,
        candidates=tuple(passages),
    )
