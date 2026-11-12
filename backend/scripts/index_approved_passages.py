"""Create the versioned Typesense collection and index approved passages only.

Run from backend/: ``uv run python -m scripts.index_approved_passages``.
The input file is a local review record. It is never fetched from the web.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from typesense.exceptions import TypesenseClientError

from app.core.config import Settings
from app.schemas.knowledge import CuratedPassage, PassageReviewStatus
from app.services.knowledge import (
    SOURCES_DIR,
    is_eligible_for_production_retrieval,
    load_registry,
)
from app.services.typesense_store import (
    InvalidIndexedPassage,
    TypesenseKnowledgeStore,
    TypesenseSchemaMismatch,
    TypesenseUnavailable,
    create_typesense_client,
    make_index_document,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_PASSAGE_FILE = DATA_DIR / "approved" / "passages.json"


def _load_records(path: Path) -> list[Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"passages"}:
        raise ValueError("Passage file must contain only a 'passages' list")
    if not isinstance(raw["passages"], list):
        raise ValueError("'passages' must be a list")
    return raw["passages"]


def _load_sources() -> dict[str, Any]:
    sources: dict[str, Any] = {}
    for path in sorted(SOURCES_DIR.glob("*.json")):
        registry = load_registry(path)
        for source in registry.sources:
            if source.id in sources:
                raise ValueError(f"Duplicate source ID in registry: {source.id}")
            sources[source.id] = source
    return sources


async def index_file(path: Path, settings: Settings) -> dict[str, Any]:
    report: dict[str, Any] = {
        "indexed": 0,
        "removed": 0,
        "skipped": [],
        "failed": [],
    }
    records = _load_records(path)
    sources = _load_sources()
    client = create_typesense_client(settings)
    try:
        store = TypesenseKnowledgeStore(client, settings.typesense_collection)
        created = await store.ensure_collection()
        report["collection_created"] = created
        approved_ids: set[str] = set()
        for index, raw in enumerate(records):
            try:
                record = CuratedPassage.model_validate(raw)
            except ValidationError:
                report["failed"].append(
                    {"record": index, "reason": "Invalid passage review metadata."}
                )
                continue
            source = sources.get(record.source_id)
            if source is None:
                report["failed"].append(
                    {
                        "record": index,
                        "source_id": record.source_id,
                        "reason": "Unknown source.",
                    }
                )
                continue
            if record.topic is not source.topic:
                report["failed"].append(
                    {
                        "record": index,
                        "source_id": record.source_id,
                        "reason": "Passage topic does not match source registry.",
                    }
                )
                continue
            if record.review_status is not PassageReviewStatus.APPROVED:
                report["skipped"].append(
                    {
                        "record": index,
                        "source_id": record.source_id,
                        "reason": record.review_status.value,
                    }
                )
                continue
            if not is_eligible_for_production_retrieval(source):
                report["skipped"].append(
                    {
                        "record": index,
                        "source_id": record.source_id,
                        "reason": "Source permission or source review is not eligible.",
                    }
                )
                continue
            try:
                document = make_index_document(record, source)
                await store.upsert(document)
            except (TypesenseUnavailable, TypesenseClientError):
                report["failed"].append(
                    {
                        "record": index,
                        "source_id": record.source_id,
                        "reason": "Typesense indexing failed.",
                    }
                )
                continue
            approved_ids.add(document["id"])
            report["indexed"] += 1
        report["removed"] = await store.prune_unapproved(approved_ids)
        if report["indexed"] == 0:
            report["message"] = "No eligible approved passages were indexed."
        return report
    finally:
        await client.api_call.aclose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--file", type=Path, default=DEFAULT_PASSAGE_FILE)
    args = parser.parse_args(argv)
    try:
        report = asyncio.run(index_file(args.file, Settings()))
    except (
        OSError,
        ValueError,
        TypesenseClientError,
        InvalidIndexedPassage,
        TypesenseSchemaMismatch,
        TypesenseUnavailable,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
