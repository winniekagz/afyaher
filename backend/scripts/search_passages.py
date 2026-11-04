"""Search the synthetic fixture passages from the command line.

Usage (from backend/):
    uv run python -m scripts.search_passages "green lanterns" [--limit N]

Development only: searches data/fixtures/synthetic with the
development_only scope. Results are fictional and are not evidence.
The query is used in memory only and is never written anywhere.
"""

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from app.schemas.educational import Topic
from app.schemas.knowledge import ContentScope
from app.services.knowledge import SYNTHETIC_DIR, load_registry
from app.services.retrieval import (
    DEFAULT_LIMIT,
    RetrievalError,
    load_passage_sets,
    retrieve,
)

PREVIEW_CHARS = 100


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--fixtures", type=Path, default=SYNTHETIC_DIR)
    args = parser.parse_args(argv)

    try:
        registry = load_registry(args.fixtures / "registry.json")
        passage_sets = load_passage_sets(args.fixtures / "passages")
        results = retrieve(
            args.query,
            Topic(registry.topic),
            registry,
            passage_sets,
            scope=ContentScope.DEVELOPMENT_ONLY,
            limit=args.limit,
        )
    except (OSError, ValidationError, RetrievalError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("DEVELOPMENT ONLY — synthetic fixtures, not medical evidence.")
    if not results:
        print("No matching passages (insufficient evidence).")
        return 0
    for result in results:
        passage = result.passage
        preview = passage.text[:PREVIEW_CHARS]
        if len(passage.text) > PREVIEW_CHARS:
            preview += "…"
        print(f"- {passage.id}  source={passage.source_id}  score={result.score}")
        print(f"    matched: {', '.join(result.matched_terms)}")
        print(f"    {preview}")
    print(f"{len(results)} passage(s) returned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
