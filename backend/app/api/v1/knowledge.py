"""Catalogue metadata only; never fetches publishers or invokes a model."""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.catalogue import CatalogueSource, SourceCatalogue
from app.schemas.educational import Topic
from app.schemas.retrieval import (
    EvidenceSufficiency,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    RetrievalStatus,
)
from app.services.knowledge import (
    APPROVED_PASSAGES_FILE,
    SOURCES_DIR,
    load_registry,
)
from app.services.knowledge_search import (
    load_approved_material,
    search_approved_knowledge,
)
from app.services.typesense_store import (
    InvalidIndexedPassage,
    TypesenseKnowledgeStore,
    TypesenseUnavailable,
    create_typesense_client,
)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get(
    "/sources",
    response_model=SourceCatalogue,
    summary="List source metadata and review status",
    description=(
        "Returns local registry metadata only, including unreviewed candidates. "
        "Listing is not ingestion permission, clinical approval or claim support. "
        "No publisher download, passage retrieval or LLM call occurs. "
        "Supported topics without a registry return an empty list."
    ),
    responses={503: {"description": "Source catalogue unavailable"}},
)
def sources(topic: Topic, response: Response) -> SourceCatalogue:
    response.headers["Cache-Control"] = "no-store"
    registry_path = SOURCES_DIR / f"{topic.value}.json"
    if not registry_path.exists():
        return SourceCatalogue(topic=topic, sources=[])
    try:
        registry = load_registry(registry_path)
        if registry.topic != topic:
            raise ValueError("Registry topic mismatch")
        return SourceCatalogue(
            topic=topic,
            sources=[
                CatalogueSource.model_validate(
                    source.model_dump(include=set(CatalogueSource.model_fields))
                )
                for source in registry.sources
            ],
        )
    except (OSError, ValueError, ValidationError):
        raise HTTPException(
            status_code=503,
            detail="Source catalogue unavailable",
            headers={"Cache-Control": "no-store"},
        ) from None


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Search approved passages without generating an answer",
    description=(
        "Searches Typesense with an exact topic filter and returns provenance-checked "
        "passage candidates. A search match is not claim-support validation. Empty "
        "results abstain; Typesense failures return retrieval_unavailable. "
        "No LLM is called."
    ),
    responses={
        503: {"model": KnowledgeSearchResponse, "description": "Retrieval unavailable"}
    },
)
async def search_knowledge(
    request_body: KnowledgeSearchRequest,
    request: Request,
    response: Response,
) -> KnowledgeSearchResponse:
    response.headers["Cache-Control"] = "no-store"
    settings: Settings = request.app.state.settings
    client = None
    try:
        client = create_typesense_client(settings)
        store = TypesenseKnowledgeStore(client, settings.typesense_collection)
        sources_by_id, approved_passages = load_approved_material(
            SOURCES_DIR, APPROVED_PASSAGES_FILE
        )
        return await search_approved_knowledge(
            request_body.question,
            request_body.topic,
            sources_by_id,
            approved_passages,
            store,
            request_body.limit,
        )
    except (
        TypesenseUnavailable,
        InvalidIndexedPassage,
        OSError,
        ValueError,
        ValidationError,
    ):
        response.status_code = 503
        return KnowledgeSearchResponse(
            status=RetrievalStatus.RETRIEVAL_UNAVAILABLE,
            topic=request_body.topic,
            evidence_sufficiency=EvidenceSufficiency.INSUFFICIENT,
            passages=[],
            reason="Approved knowledge retrieval is temporarily unavailable.",
        )
    finally:
        if client is not None:
            await client.api_call.aclose()
