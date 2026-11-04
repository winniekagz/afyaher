"""Validate and summarise a source registry.

Usage (from backend/):
    uv run python -m scripts.inspect_sources [path/to/registry.json]

Defaults to data/sources/pcos.json. Exits 1 if the registry is invalid.
"""

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from app.services.knowledge import SOURCES_DIR, is_eligible_for_ingestion, load_registry

DEFAULT_REGISTRY = SOURCES_DIR / "pcos.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args(argv)

    try:
        registry = load_registry(args.path)
    except OSError as exc:
        print(f"ERROR: cannot read registry {args.path}: {exc}", file=sys.stderr)
        return 1
    except ValidationError as exc:
        print(f"ERROR: invalid registry {args.path}:\n{exc}", file=sys.stderr)
        return 1

    print(f"Registry: {args.path} (topic: {registry.topic})")
    for source in registry.sources:
        print(f"- {source.id}")
        print(f"    title:           {source.title}")
        print(f"    publisher:       {source.publisher}")
        print(f"    evidence type:   {source.evidence_type}")
        print(f"    scope:           {source.content_scope}")
        print(f"    clinical review: {source.clinical_review_status}")
        print(f"    permission:      {source.ingestion_permission}")
        print(f"    ingestion:       {source.ingestion_status}")
    print(f"Total sources: {len(registry.sources)}")

    not_eligible = [s.id for s in registry.sources if not is_eligible_for_ingestion(s)]
    if not_eligible:
        print(f"Not approved for ingestion ({len(not_eligible)}):")
        for source_id in not_eligible:
            print(f"- {source_id}")
    else:
        print("All sources are approved for ingestion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
