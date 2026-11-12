"""Read-only public projection of source metadata, never article text."""

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.schemas.educational import Topic
from app.schemas.knowledge import (
    ClinicalReviewStatus,
    ContentScope,
    IngestionPermission,
    IngestionStatus,
    SourceId,
)


class CatalogueSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: SourceId
    topic: Topic
    title: str
    publisher: str
    url: HttpUrl
    clinical_review_status: ClinicalReviewStatus
    ingestion_permission: IngestionPermission
    ingestion_status: IngestionStatus
    content_scope: ContentScope


class SourceCatalogue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Topic
    sources: list[CatalogueSource]
