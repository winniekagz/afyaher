"""Flow 01's deliberately abstention-only contract, pending clinical evidence."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.educational import EducationalResponse, SourceReference, Topic


class QuestionStatus(StrEnum):
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CLARIFICATION_NEEDED = "clarification_needed"
    OUT_OF_SCOPE = "out_of_scope"
    URGENT_GUIDANCE = "urgent_guidance"
    SERVICE_UNAVAILABLE = "service_unavailable"


class QuestionReason(StrEnum):
    URGENT_NOTICE = "urgent_notice"
    PERSONAL_ADVICE = "personal_advice"
    UNSUPPORTED_TOPIC = "unsupported_topic"
    TOPIC_MISMATCH = "topic_mismatch"
    CLARIFY_TOPIC = "clarify_topic"
    NO_APPROVED_EVIDENCE = "no_approved_evidence"
    RETRIEVAL_UNAVAILABLE = "retrieval_unavailable"
    VERIFICATION_UNAVAILABLE = "verification_unavailable"


class QuestionResponse(BaseModel):
    """No raw-question echo, generated claims or citations can be published.

    A future answered contract requires independent claim verification. Do not
    loosen these constraints merely because retrieval returned valid passage IDs.
    """

    model_config = ConfigDict(extra="forbid")

    status: QuestionStatus
    reason: QuestionReason
    topic: Topic
    short_answer: str
    key_points: list[str] = Field(default_factory=list, max_length=0)
    uncertainties: list[str]
    citations: list[SourceReference] = Field(default_factory=list, max_length=0)
    next_steps: list[str]
    suggested_clinician_questions: list[str]
    grounding: Literal["not_established"] = "not_established"
    disclaimer: str = EducationalResponse.model_fields["disclaimer"].default
