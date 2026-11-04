from typing import Annotated

from fastapi import APIRouter, Body

from app.schemas.educational import (
    EducationalRequest,
    EducationalResponse,
)

router = APIRouter(prefix="/api/v1", tags=["education"])


@router.post(
    "/education/ask",
    response_model=EducationalResponse,
    summary="Validate an educational question (unavailable stub)",
    response_description=(
        "HTTP 200 with application status service_unavailable; no medical answer "
        "or citations. This is not an HTTP 503 response."
    ),
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "service_unavailable",
                        "topic": "pcos",
                        "question": "A synthetic educational question for testing.",
                        "answer": "Educational answers are not available yet.",
                        "sources": [],
                        "limitations": (
                            "The evidence-backed answer service is not implemented."
                        ),
                        "disclaimer": (
                            "This is educational information, not medical advice. "
                            "Consult a qualified clinician for personal "
                            "health decisions."
                        ),
                    }
                }
            }
        },
        422: {
            "description": (
                "Request validation failed: unsupported topic, wrong types, missing "
                "or extra fields, fewer than three non-whitespace characters, or "
                "more than 2,000 characters after trimming. Framework errors may "
                "echo input values; use synthetic data only."
            )
        },
        405: {"description": "The requested method is not supported by this path."},
    },
)
def ask(
    request: Annotated[
        EducationalRequest,
        Body(
            description=(
                "Only topic and question are accepted. The question must be a string; "
                "leading/trailing whitespace is removed before checking at least "
                "three non-whitespace characters and at most 2,000 total characters. "
                "Do not send identifying information or real health questions."
            ),
            openapi_examples={
                "synthetic_pcos": {
                    "summary": "Synthetic PCOS routing example (not medical content)",
                    "value": {
                        "topic": "pcos",
                        "question": "A synthetic educational question for testing.",
                    },
                },
                "synthetic_cysts": {
                    "summary": "Synthetic ovarian-cysts routing example",
                    "value": {
                        "topic": "ovarian-cysts",
                        "question": "Another fictional request for an API test.",
                    },
                },
                "synthetic_torsion": {
                    "summary": "Synthetic ovarian-torsion routing example",
                    "value": {
                        "topic": "ovarian-torsion",
                        "question": "A fictional topic-routing request for testing.",
                    },
                },
            },
        ),
    ],
) -> EducationalResponse:
    """Accept an educational question and return a stub response.

    No AI provider, retrieval pipeline, or safety screening is connected.
    Every question receives an explicit service-unavailable status
    until the retrieval and generation layers are implemented.
    """
    return EducationalResponse(
        status="service_unavailable",
        topic=request.topic,
        question=request.question,
        answer="Educational answers are not available yet.",
        sources=[],
        limitations=("The evidence-backed answer service is not implemented."),
    )
