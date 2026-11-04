"""Deterministic keyword retrieval over locally stored passages.

A placeholder for vector search: no embeddings, database, or network.
It exists so retrieval -> citation resolution can be tested end to end.

Scope controls which sources are searchable:

- ``production``: only sources passing ``is_eligible_for_production_retrieval``.
- ``development_only``: sources passing ``can_chunk``, which includes
  synthetic fixtures. Results are never valid user-facing evidence.

Queries are processed in memory only; they are never logged or stored.
"""

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from app.schemas.educational import Topic
from app.schemas.knowledge import (
    ContentScope,
    PassageSet,
    RetrievedPassage,
    SourcePassage,
    SourceRegistry,
)
from app.services.knowledge import can_chunk, is_eligible_for_production_retrieval

DEFAULT_LIMIT = 3
MAX_LIMIT = 20
MAX_QUERY_CHARS = 2000

# Japanese and Chinese have no spaces between words, so runs of these
# scripts are indexed as overlapping character pairs (bigrams).
_CJK_RUN = r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]+"
_TOKEN = re.compile(rf"{_CJK_RUN}|\w+")
_IS_CJK = re.compile(rf"^{_CJK_RUN}$")
_STOPWORDS = frozenset(
    "a an and are as at be but by can do does for from has have how i if in is "
    "it its me my of on or so that the their there these this to was what when "
    "where which who why will with you your".split()
)


class RetrievalError(ValueError):
    """Raised for invalid queries or inconsistent passage data."""


def tokenize(text: str) -> list[str]:
    """Return casefolded search terms, excluding common English stopwords."""
    normalised = unicodedata.normalize("NFKC", text).casefold()
    terms: list[str] = []
    for token in _TOKEN.findall(normalised):
        if _IS_CJK.match(token):
            terms.extend(token[i : i + 2] for i in range(max(1, len(token) - 1)))
        elif token not in _STOPWORDS:
            terms.append(token)
    return terms


def load_passage_sets(directory: Path) -> list[PassageSet]:
    """Load and validate every ``*.json`` passage set in a directory."""
    return [
        PassageSet.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(directory.glob("*.json"))
    ]


def _searchable_passages(
    registry: SourceRegistry, passage_sets: Iterable[PassageSet], scope: ContentScope
) -> list[SourcePassage]:
    sources = {s.id: s for s in registry.sources}
    allowed = (
        is_eligible_for_production_retrieval
        if scope is ContentScope.PRODUCTION
        else can_chunk
    )
    passages: list[SourcePassage] = []
    seen_sources: set[str] = set()
    for passage_set in passage_sets:
        source = sources.get(passage_set.source_id)
        if source is None:
            raise RetrievalError(
                f"Passages reference unknown source '{passage_set.source_id}'"
            )
        if passage_set.source_id in seen_sources:
            raise RetrievalError(f"Duplicate passage set for '{source.id}'")
        seen_sources.add(source.id)
        if passage_set.content_scope is not source.content_scope:
            raise RetrievalError(f"Passage set scope does not match '{source.id}'")
        if not can_chunk(source):
            raise RetrievalError(f"Passages exist for unchunkable source '{source.id}'")
        if any(p.topic is not source.topic for p in passage_set.passages):
            raise RetrievalError(f"Passage topic does not match '{source.id}'")
        if allowed(source):
            passages.extend(passage_set.passages)
    return passages


def retrieve(
    query: str,
    topic: Topic,
    registry: SourceRegistry,
    passage_sets: Iterable[PassageSet],
    scope: ContentScope = ContentScope.PRODUCTION,
    limit: int = DEFAULT_LIMIT,
) -> list[RetrievedPassage]:
    """Return up to ``limit`` passages ranked by distinct matched terms.

    Ties break on total term occurrences, then source ID and position, so
    results are deterministic. Returns ``[]`` when nothing matches; callers
    must treat that as insufficient evidence, never as a reason to answer
    without sources. Defaults to the production scope.
    """
    try:
        scope = ContentScope(scope)
    except (TypeError, ValueError) as exc:
        raise RetrievalError("Unknown retrieval scope") from exc
    if not query.strip():
        raise RetrievalError("Query is empty")
    if len(query) > MAX_QUERY_CHARS:
        raise RetrievalError(f"Query exceeds {MAX_QUERY_CHARS} characters")
    if not 1 <= limit <= MAX_LIMIT:
        raise RetrievalError(f"limit must be between 1 and {MAX_LIMIT}")

    candidates = _searchable_passages(registry, passage_sets, scope)
    query_terms = set(tokenize(query))
    if not query_terms:
        return []

    scored: list[tuple[int, int, SourcePassage, list[str]]] = []
    for passage in candidates:
        if passage.topic is not topic:
            continue
        counts = Counter(tokenize(passage.text))
        matched = sorted(term for term in query_terms if term in counts)
        if matched:
            occurrences = sum(counts[term] for term in matched)
            scored.append((len(matched), occurrences, passage, matched))

    scored.sort(key=lambda s: (-s[0], -s[1], s[2].source_id, s[2].position))
    return [
        RetrievedPassage(passage=passage, score=score, matched_terms=matched)
        for score, _, passage, matched in scored[:limit]
    ]
