"""Schemas for the AfyaHer source registry.

The registry stores source metadata only — never article content.
Clinical review status and legal ingestion permission are deliberately
separate fields: a clinically sound source may still be copyrighted, and
a permissively licensed source may still be clinically unreviewed.

Unverified facts are recorded explicitly: date, license, and authorization
fields are required keys whose value is ``null`` when they have not been
verified.

``content_scope`` separates synthetic development fixtures from material
intended for production evidence. Synthetic fixtures are always
``development_only`` and can never be production evidence.

``SourcePassage`` describes a chunk of text that will eventually be stored
for retrieval. Every passage points back to its registry source so each
citation can be traced to a publisher, URL, and review status.
"""

from collections import Counter
from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator,
)

from app.schemas.educational import Topic

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
SourceId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]


class EvidenceType(StrEnum):
    FACT_SHEET = "fact_sheet"
    CLINICAL_GUIDELINE = "clinical_guideline"
    PATIENT_LEAFLET = "patient_leaflet"
    SYSTEMATIC_REVIEW = "systematic_review"
    SYNTHETIC_FIXTURE = "synthetic_fixture"


class ContentScope(StrEnum):
    DEVELOPMENT_ONLY = "development_only"
    PRODUCTION = "production"


class ClinicalReviewStatus(StrEnum):
    NOT_REVIEWED = "not_reviewed"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class IngestionPermission(StrEnum):
    NOT_VERIFIED = "not_verified"
    PERMITTED = "permitted"
    PROHIBITED = "prohibited"


class IngestionStatus(StrEnum):
    METADATA_ONLY = "metadata_only"
    INGESTED = "ingested"


class KnowledgeSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: SourceId
    topic: Topic
    title: NonEmptyStr
    publisher: NonEmptyStr
    url: HttpUrl
    evidence_type: EvidenceType
    # Legacy metadata remains readable, but production evidence requires
    # an explicit production scope rather than an implicit promotion.
    content_scope: ContentScope = ContentScope.DEVELOPMENT_ONLY
    publication_date: date | None
    last_verified_date: date | None
    clinical_review_status: ClinicalReviewStatus
    ingestion_permission: IngestionPermission
    license: NonEmptyStr | None
    authorization_reference: NonEmptyStr | None = Field(
        description="Where permission is evidenced: license URL or permission record"
    )
    authorization_date: date | None
    ingestion_status: IngestionStatus

    @model_validator(mode="after")
    def check_consistency(self) -> "KnowledgeSource":
        if (
            self.evidence_type is EvidenceType.SYNTHETIC_FIXTURE
            and self.content_scope is not ContentScope.DEVELOPMENT_ONLY
        ):
            raise ValueError(
                "evidence_type 'synthetic_fixture' requires content_scope "
                "'development_only'"
            )
        if self.ingestion_permission is IngestionPermission.PERMITTED:
            missing = [
                name
                for name in ("license", "authorization_reference", "authorization_date")
                if getattr(self, name) is None
            ]
            if missing:
                raise ValueError(
                    f"ingestion_permission 'permitted' requires {', '.join(missing)}"
                )
        if self.ingestion_status is IngestionStatus.INGESTED and not (
            self.ingestion_permission is IngestionPermission.PERMITTED
            and self.clinical_review_status is ClinicalReviewStatus.APPROVED
        ):
            raise ValueError(
                "ingestion_status 'ingested' requires permitted ingestion and "
                "approved clinical review"
            )
        return self


class SourceRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Topic
    sources: list[KnowledgeSource]

    @model_validator(mode="after")
    def check_sources(self) -> "SourceRegistry":
        duplicates = sorted(
            source_id
            for source_id, count in Counter(s.id for s in self.sources).items()
            if count > 1
        )
        if duplicates:
            raise ValueError(f"Duplicate source IDs: {', '.join(duplicates)}")

        mismatched = sorted(s.id for s in self.sources if s.topic != self.topic)
        if mismatched:
            raise ValueError(
                f"Sources do not match registry topic '{self.topic}': "
                f"{', '.join(mismatched)}"
            )
        return self


MAX_PASSAGE_CHARS = 4000


class SourcePassage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: SourceId
    source_id: SourceId
    topic: Topic
    position: int = Field(ge=0)
    text: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=MAX_PASSAGE_CHARS
        ),
    ]


class PassageSet(BaseModel):
    """All passages generated from one source, as written to local JSON."""

    model_config = ConfigDict(extra="forbid")

    source_id: SourceId
    content_scope: ContentScope
    max_chars: int = Field(ge=1, le=MAX_PASSAGE_CHARS)
    passages: list[SourcePassage] = Field(min_length=1)

    @model_validator(mode="after")
    def check_passages(self) -> "PassageSet":
        if any(len(p.text) > self.max_chars for p in self.passages):
            raise ValueError("Passage text exceeds passage set max_chars")
        foreign = sorted({p.source_id for p in self.passages} - {self.source_id})
        if foreign:
            raise ValueError(f"Passages reference other sources: {', '.join(foreign)}")
        if [p.position for p in self.passages] != list(range(len(self.passages))):
            raise ValueError("Passage positions must be sequential from 0")
        expected = [f"{self.source_id}-p{p.position}" for p in self.passages]
        if [p.id for p in self.passages] != expected:
            raise ValueError("Passage IDs must be '<source_id>-p<position>'")
        return self


class RetrievedPassage(BaseModel):
    """A passage returned by retrieval, with its lexical relevance score."""

    model_config = ConfigDict(extra="forbid")

    passage: SourcePassage
    score: int = Field(ge=1, description="Number of distinct query terms matched")
    matched_terms: list[str] = Field(min_length=1)
