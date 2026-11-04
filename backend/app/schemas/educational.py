"""Schemas for the educational question API.

Request validation enforces:
- String type (no coercion from int, list, etc.)
- Whitespace trimming before constraint checks
- At least 3 non-whitespace characters
- Maximum 2,000 characters after trimming
- No unexpected fields

Source URLs are validated with Pydantic's HttpUrl. Note that HttpUrl
normalises bare domains by appending a trailing slash
(e.g. "https://example.com" → "https://example.com/"). All current
AfyaHer sources use full paths, so this does not affect them. If a
bare-domain source is added later, the trailing slash must be accounted
for in any frontend equality checks.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class Topic(StrEnum):
    PCOS = "pcos"
    OVARIAN_CYSTS = "ovarian-cysts"
    OVARIAN_TORSION = "ovarian-torsion"


class EducationalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: Topic
    question: str = Field(
        max_length=2000,
        description="A question containing at least 3 non-whitespace characters",
    )

    @field_validator("question", mode="before")
    @classmethod
    def validate_question(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("Question must be a string")

        stripped = value.strip()
        non_ws = sum(1 for ch in stripped if not ch.isspace())

        if non_ws < 3:
            raise ValueError(
                "Question must contain at least 3 non-whitespace characters"
            )

        return stripped


class AnswerStatus(StrEnum):
    ANSWERED = "answered"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CLARIFICATION_NEEDED = "clarification_needed"
    OUT_OF_SCOPE = "out_of_scope"
    URGENT_GUIDANCE = "urgent_guidance"
    SERVICE_UNAVAILABLE = "service_unavailable"


class SourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    publisher: str
    url: HttpUrl


class EducationalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AnswerStatus
    topic: Topic
    question: str
    answer: str
    sources: list[SourceReference]
    limitations: str | None = Field(
        default=None,
        description="Explicit limitation or abstention when evidence is insufficient",
    )
    disclaimer: Literal[
        "This is educational information, not medical advice. "
        "Consult a qualified clinician for personal health decisions."
    ] = (
        "This is educational information, not medical advice. "
        "Consult a qualified clinician for personal health decisions."
    )
