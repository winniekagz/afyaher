"""Conservative private-prototype interruptions, NOT a symptom assessment.

No negation, temporal, language or clinical completeness is claimed. Non-matches
never imply safety. Every UI must also show static urgent guidance. Rules and
wording need qualified clinical review before any real-user deployment.
"""

import re
import unicodedata

from app.schemas.educational import EducationalRequest, Topic
from app.schemas.questions import QuestionReason

URGENT_GUIDANCE = (
    "Sudden, severe pelvic or lower abdominal pain, especially with nausea or "
    "vomiting, needs urgent medical evaluation. Seek emergency care now rather "
    "than waiting for AfyaHer. This notice cannot diagnose, assess or rule out "
    "an emergency."
)

_TOPICS = {
    Topic.PCOS: re.compile(r"\b(pcos|polycystic ovar(?:y|ian) syndrome)\b"),
    Topic.OVARIAN_CYSTS: re.compile(r"\b(?:ovarian |ovary )?cysts?\b"),
    Topic.OVARIAN_TORSION: re.compile(r"\b(?:ovarian )?torsion\b"),
}


def screen_question(request: EducationalRequest) -> QuestionReason | None:
    text = unicodedata.normalize("NFKC", request.question).casefold()
    location = re.search(r"\b(pelvic|abdomen|abdominal|stomach|tummy)\b", text)
    pain = re.search(r"\b(pain|hurts?|cramp(?:s|ing)?)\b", text)
    urgent = re.search(
        r"\b(sudden(?:ly)?|severe|unbearable|intense|vomit\w*|nause\w*|sick)\b",
        text,
    )
    if (location and pain and urgent) or re.search(
        r"\b(?:suspect\w*|might have|may have|think .{0,15}have)\b.{0,30}\btorsion\b",
        text,
    ):
        return QuestionReason.URGENT_NOTICE
    if re.search(
        r"\b(do i need|should i|do i have|am i|diagnose|diagnosis for me|"
        r"my symptoms|my (?:scan|test)|what (?:medicine|medication|dose)|"
        r"which (?:treatment|medication)|will i|can i get pregnant)\b",
        text,
    ) or (re.search(r"\b(i|my)\b", text) and pain):
        return QuestionReason.PERSONAL_ADVICE
    mentioned = {topic for topic, pattern in _TOPICS.items() if pattern.search(text)}
    if mentioned and request.topic not in mentioned:
        return QuestionReason.TOPIC_MISMATCH
    if mentioned:
        return None
    if re.search(r"\b(that|it|this|more|follow.?up)\b", text):
        return QuestionReason.CLARIFY_TOPIC
    return QuestionReason.UNSUPPORTED_TOPIC
