"""Conventional request-response question flow, with no streaming."""

from fastapi import APIRouter, Request, Response

from app.schemas.educational import EducationalRequest
from app.schemas.questions import QuestionResponse, QuestionStatus
from app.services.questions import answer_question

router = APIRouter(prefix="/api/v1", tags=["education"])


@router.post(
    "/questions",
    response_model=QuestionResponse,
    summary="Ask a general educational question (safe fallback phase)",
    description=(
        "Validates input, interrupts recognized urgent wording before retrieval, "
        "and checks scope. Uses the existing approved Typesense retrieval path. "
        "No approved medical corpus or claim-level verifier is available: this "
        "phase never publishes an answered status, generated claims or citations. "
        "Each question is independent. Use synthetic scenarios only."
    ),
    responses={
        413: {"description": "Body exceeds 16 KiB"},
        422: {"description": "Invalid request; raw input is not echoed"},
        429: {"description": "Local per-client question rate limit reached"},
        503: {"model": QuestionResponse, "description": "Evidence service unavailable"},
    },
)
async def ask_question(
    body: EducationalRequest, request: Request, response: Response
) -> QuestionResponse:
    response.headers["Cache-Control"] = "no-store"
    result = await answer_question(body, request.app.state.settings)
    if result.status is QuestionStatus.SERVICE_UNAVAILABLE:
        response.status_code = 503
    return result
