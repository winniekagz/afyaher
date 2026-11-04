"""Chunk development-only synthetic fixtures into local passage JSON.

Usage (from backend/):
    uv run python -m scripts.build_passages [--registry PATH] [--out-dir PATH]

Reads <registry>, then <source_id>.txt beside it for each source, and writes
<out-dir>/<source_id>.json. Only synthetic fixtures scoped development_only
are accepted; real sources are refused so their content never lands in
development output. Exits 1 on any validation or eligibility error.
"""

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from app.schemas.knowledge import ContentScope, PassageSet
from app.services.chunking import chunk_text
from app.services.knowledge import (
    SYNTHETIC_DIR,
    can_chunk,
    is_eligible_for_production_retrieval,
    is_synthetic_fixture,
    load_registry,
)

# Smaller than the chunker default so the short fixture yields several
# passages, which exercises multi-passage citation traceability.
FIXTURE_MAX_CHARS = 400


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--registry", type=Path, default=SYNTHETIC_DIR / "registry.json"
    )
    parser.add_argument("--out-dir", type=Path, default=SYNTHETIC_DIR / "passages")
    parser.add_argument("--max-chars", type=int, default=FIXTURE_MAX_CHARS)
    args = parser.parse_args(argv)

    try:
        registry = load_registry(args.registry)
    except (OSError, ValidationError) as exc:
        print(f"ERROR: invalid registry {args.registry}:\n{exc}", file=sys.stderr)
        return 1

    results: list[PassageSet] = []
    for source in registry.sources:
        if not (
            is_synthetic_fixture(source)
            and source.content_scope is ContentScope.DEVELOPMENT_ONLY
            and can_chunk(source)
            and not is_eligible_for_production_retrieval(source)
        ):
            print(
                f"ERROR: '{source.id}' is not a development-only synthetic fixture",
                file=sys.stderr,
            )
            return 1
        text_path = args.registry.parent / f"{source.id}.txt"
        try:
            text = text_path.read_text(encoding="utf-8")
            passages = chunk_text(source, text, max_chars=args.max_chars)
            results.append(
                PassageSet(
                    source_id=source.id,
                    content_scope=source.content_scope,
                    max_chars=args.max_chars,
                    passages=passages,
                )
            )
        except (OSError, ValueError) as exc:
            print(
                f"ERROR: cannot build passages for '{source.id}': {exc}",
                file=sys.stderr,
            )
            return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for passage_set in results:
        out_path = args.out_dir / f"{passage_set.source_id}.json"
        out_path.write_text(
            passage_set.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        print(f"{passage_set.source_id} [{passage_set.content_scope}] -> {out_path}")
        for passage in passage_set.passages:
            print(f"  {passage.id}  ({len(passage.text)} chars)")
    total = sum(len(r.passages) for r in results)
    print(f"Built {total} passages from {len(results)} source(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
