"""API models for retrieval candidates and explicit evidence abstention."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.schemas.educational import EducationalRequest, Topic


class KnowledgeSearchRequest(EducationalRequest):
    limit: int = Field(default=5, ge=1, le=10)


class RetrievalStatus(StrEnum):
    CANDIDATES_FOUND = "candidates_found"
    NO_MATCHING_EVIDENCE = "no_matching_evidence"
    RETRIEVAL_UNAVAILABLE = "retrieval_unavailable"


class EvidenceSufficiency(StrEnum):
    NOT_ASSESSED = "not_assessed"
    INSUFFICIENT = "insufficient"


class KnowledgeSearchHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_id: str
    source_title: str
    source_url: HttpUrl
    topic: Topic
    section: str
    passage: str
    publication_date: int | None
    score: int = Field(ge=0, description="Search ranking only; not evidence strength")
    content_hash: str


class KnowledgeSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: RetrievalStatus
    topic: Topic
    evidence_sufficiency: EvidenceSufficiency
    passages: list[KnowledgeSearchHit]
    reason: str | None = None
