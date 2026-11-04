"""Split source text into passages.

This module does not fetch content. Callers must supply text they are
permitted to process. Chunking refuses sources rejected by ``can_chunk``:
only eligible real sources and development-only synthetic fixtures pass.
Being chunkable does not make a source eligible for production retrieval.
"""

import re

from app.schemas.knowledge import MAX_PASSAGE_CHARS, KnowledgeSource, SourcePassage
from app.services.knowledge import can_chunk

DEFAULT_MAX_CHARS = 1200
_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?…])\s+|(?<=[。！？])(?![。！？])\s*")


class IneligibleSourceError(ValueError):
    """Raised when content is offered for a source that may not be chunked."""


class EmptyContentError(ValueError):
    """Raised when source text contains no non-whitespace characters."""


def _sentences(paragraph: str) -> list[str]:
    """Split a paragraph into sentences, each keeping its trailing separator.

    Concatenating the result reproduces ``paragraph`` exactly.
    """
    units: list[str] = []
    start = 0
    for match in _SENTENCE_BOUNDARY.finditer(paragraph):
        if match.end() > start:
            units.append(paragraph[start : match.end()])
            start = match.end()
    if start < len(paragraph):
        units.append(paragraph[start:])
    return units


def _split_long(paragraph: str, max_chars: int) -> list[str]:
    """Split one whitespace-normalised paragraph into pieces of <= max_chars.

    Sentences are packed while they fit. A sentence longer than max_chars
    is split at the last space that fits, or hard-split at max_chars.
    """
    pieces: list[str] = []
    current = ""
    for unit in _sentences(paragraph):
        if len((current + unit).rstrip()) <= max_chars:
            current += unit
            continue
        if current.strip():
            pieces.append(current.strip())
        while len(unit.rstrip()) > max_chars:
            cut = unit.rfind(" ", 0, max_chars + 1)
            cut = cut if cut > 0 else max_chars
            pieces.append(unit[:cut].strip())
            unit = unit[cut:].lstrip()
        current = unit
    if current.strip():
        pieces.append(current.strip())
    return pieces


def chunk_text(
    source: KnowledgeSource, text: str, max_chars: int = DEFAULT_MAX_CHARS
) -> list[SourcePassage]:
    """Return ordered passages of at most ``max_chars`` characters.

    Paragraphs are packed together while they fit; oversized paragraphs
    are split on sentence boundaries, then on whitespace.

    Content-preservation invariant: every non-whitespace character of
    ``text`` appears in the passages, in order, exactly once. Whitespace is
    normalised (runs inside a paragraph become one space; paragraphs are
    joined by a blank line), so original formatting is not preserved.

    Raises IneligibleSourceError, then ValueError for an invalid
    ``max_chars``, then EmptyContentError for blank text, in that order.
    """
    if not can_chunk(source):
        raise IneligibleSourceError(
            f"Source '{source.id}' is not eligible for chunking"
        )
    if type(max_chars) is not int or not 1 <= max_chars <= MAX_PASSAGE_CHARS:
        raise ValueError(
            f"max_chars must be an integer between 1 and {MAX_PASSAGE_CHARS}"
        )
    if not text.strip():
        raise EmptyContentError(f"Source '{source.id}' text is empty")

    paragraphs = [
        " ".join(p.split()) for p in _PARAGRAPH_BREAK.split(text) if p.strip()
    ]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            *full, current = _split_long(paragraph, max_chars)
            chunks.extend(full)
    if current:
        chunks.append(current)

    return [
        SourcePassage(
            id=f"{source.id}-p{position}",
            source_id=source.id,
            topic=source.topic,
            position=position,
            text=chunk,
        )
        for position, chunk in enumerate(chunks)
    ]
