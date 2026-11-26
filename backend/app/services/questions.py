"""Flow 01 orchestration; no medical generation or provider fallback."""

import asyncio

from app.core.config import Settings
from app.schemas.educational import EducationalRequest
from app.schemas.questions import QuestionReason, QuestionResponse, QuestionStatus
from app.schemas.retrieval import RetrievalStatus
from app.services.knowledge import APPROVED_PASSAGES_FILE, SOURCES_DIR
from app.services.knowledge_search import (
    load_approved_material,
    search_approved_knowledge,
)
from app.services.question_safety import URGENT_GUIDANCE, screen_question
from app.services.typesense_store import (
    InvalidIndexedPassage,
    TypesenseKnowledgeStore,
    TypesenseUnavailable,
    create_typesense_client,
)

_OUTCOMES = {
    QuestionReason.URGENT_NOTICE: (
        QuestionStatus.URGENT_GUIDANCE,
        URGENT_GUIDANCE,
        "This conservative notice is not a diagnosis or a complete emergency screen.",
    ),
    QuestionReason.PERSONAL_ADVICE: (
        QuestionStatus.OUT_OF_SCOPE,
        "AfyaHer cannot decide whether you need supplements, tests or treatment, "
        "or assess your personal symptoms or outcomes.",
        "Personal decisions require a qualified clinician; approved evidence "
        "and a clinical assessment are not available through this prototype.",
    ),
    QuestionReason.UNSUPPORTED_TOPIC: (
        QuestionStatus.OUT_OF_SCOPE,
        "This prototype covers general education about PCOS, ovarian cysts "
        "and ovarian torsion only.",
        "No answer has been generated. Rephrase as a general question naming "
        "a supported condition, or discuss the question with a clinician.",
    ),
    QuestionReason.TOPIC_MISMATCH: (
        QuestionStatus.CLARIFICATION_NEEDED,
        "Choose the condition your question is about and submit it again.",
        "The named condition differs from your selected topic. "
        "AfyaHer has not interpreted your symptoms.",
    ),
    QuestionReason.CLARIFY_TOPIC: (
        QuestionStatus.CLARIFICATION_NEEDED,
        "Please name PCOS, ovarian cysts or ovarian torsion in your question.",
        "Each submission is independent; earlier questions are not sent as context.",
    ),
    QuestionReason.NO_APPROVED_EVIDENCE: (
        QuestionStatus.INSUFFICIENT_EVIDENCE,
        "There is not enough approved evidence here to answer this question.",
        "No eligible supporting passages were available for this question. "
        "Source metadata and unreviewed examples cannot substitute for evidence.",
    ),
    QuestionReason.RETRIEVAL_UNAVAILABLE: (
        QuestionStatus.SERVICE_UNAVAILABLE,
        "The evidence service is temporarily unavailable. No answer was generated.",
        "Evidence could not be checked. AfyaHer will not use unverified "
        "sources or a model's general knowledge as a fallback.",
    ),
    QuestionReason.VERIFICATION_UNAVAILABLE: (
        QuestionStatus.INSUFFICIENT_EVIDENCE,
        "A supported answer cannot be verified yet.",
        "Retrieved candidates do not establish claim support. Medical generation "
        "and independent claim-level verification are not enabled. No passage "
        "has been presented as supporting an answer.",
    ),
}


def _outcome(request: EducationalRequest, reason: QuestionReason) -> QuestionResponse:
    status, short_answer, uncertainty = _OUTCOMES[reason]
    urgent = reason is QuestionReason.URGENT_NOTICE
    return QuestionResponse(
        status=status,
        reason=reason,
        topic=request.topic,
        short_answer=short_answer,
        uncertainties=[uncertainty],
        next_steps=(
            ["Seek emergency medical care now. Do not wait for an online response."]
            if urgent
            else [
                "Discuss personal health decisions with a qualified clinician.",
                "Inspect source review status or prepare appointment questions.",
            ]
        ),
        suggested_clinician_questions=(
            [] if urgent else ["Could you explain what information applies to me?"]
        ),
    )


async def answer_question(
    request: EducationalRequest, settings: Settings
) -> QuestionResponse:
    reason = screen_question(request)
    if reason is not None:
        return _outcome(request, reason)

    client = None
    try:
        # No connection or key is needed to establish that the corpus is empty.
        sources, approved = load_approved_material(SOURCES_DIR, APPROVED_PASSAGES_FILE)
        if not any(p.topic is request.topic for p in approved.values()):
            return _outcome(request, QuestionReason.NO_APPROVED_EVIDENCE)
        async with asyncio.timeout(4):
            client = create_typesense_client(settings)
            store = TypesenseKnowledgeStore(client, settings.typesense_collection)
            retrieved = await search_approved_knowledge(
                request.question, request.topic, sources, approved, store, 5
            )
        if retrieved.status is RetrievalStatus.NO_MATCHING_EVIDENCE:
            return _outcome(request, QuestionReason.NO_APPROVED_EVIDENCE)
        if retrieved.status is not RetrievalStatus.CANDIDATES_FOUND:
            return _outcome(request, QuestionReason.RETRIEVAL_UNAVAILABLE)
        # Fail closed even for valid IDs: no claim-level verifier exists. Do not
        # call the synthetic-only research helper, an LLM or a second retriever.
        return _outcome(request, QuestionReason.VERIFICATION_UNAVAILABLE)
    except (
        TypesenseUnavailable,
        InvalidIndexedPassage,
        OSError,
        ValueError,
        TimeoutError,
    ):
        return _outcome(request, QuestionReason.RETRIEVAL_UNAVAILABLE)
    finally:
        if client is not None:
            try:
                async with asyncio.timeout(1):
                    await client.api_call.aclose()
            except (OSError, RuntimeError, TimeoutError):
                # A cleanup failure cannot leak credentials or replace an
                # already established safe outcome with a raw exception.
                pass
