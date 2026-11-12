"""Preview synthetic retrieval; optionally select passage IDs with a free model.

From backend/: uv run python -m scripts.search_passages_with_llm 'green lanterns'
No provider call occurs unless --live and --confirm-synthetic-data are both set.
No medical documents are loaded and no output/approval records are persisted.
"""

import argparse
import os
import sys

from pydantic import ValidationError

from app.schemas.educational import Topic
from app.schemas.knowledge import ContentScope
from app.services.knowledge import SYNTHETIC_DIR, load_registry
from app.services.research_retrieval import (
    MAX_CANDIDATES,
    ResearchRetrievalError,
    list_free_models,
    select_synthetic_passages,
)
from app.services.retrieval import RetrievalError, load_passage_sets, retrieve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", nargs="?")
    parser.add_argument("--list-free-models", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-synthetic-data", action="store_true")
    args = parser.parse_args(argv)
    if args.live and not args.confirm_synthetic_data:
        print(
            "ERROR: confirm that only synthetic data will be sent remotely",
            file=sys.stderr,
        )
        return 1
    try:
        if args.list_free_models:
            for model in list_free_models():
                print(model)
            return 0
        if not args.query:
            parser.error("provide a synthetic query or --list-free-models")
        registry = load_registry(SYNTHETIC_DIR / "registry.json")
        candidates = retrieve(
            args.query,
            Topic.PCOS,
            registry,
            load_passage_sets(SYNTHETIC_DIR / "passages"),
            scope=ContentScope.DEVELOPMENT_ONLY,
            limit=MAX_CANDIDATES,
        )
        selected = [record.passage for record in candidates]
        if args.live:
            selected = select_synthetic_passages(
                args.query,
                candidates,
                registry,
                api_key=os.environ.get("AFYAHER_RESEARCH_API_KEY", ""),
                model=os.environ.get("AFYAHER_RESEARCH_MODEL", ""),
                provider=os.environ.get("AFYAHER_RESEARCH_PROVIDER", ""),
            )
        print("DEVELOPMENT ONLY: synthetic fixture IDs, not medical evidence.")
        print(
            "Mode: free hosted selection"
            if args.live
            else "Mode: lexical preview (no LLM call)"
        )
        for passage in selected:
            print(f"{passage.id} source={passage.source_id}")
        print(f"Selected {len(selected)} passage(s).")
        return 0
    except (OSError, ValueError, ValidationError, RetrievalError) as exc:
        # Do not print remote bodies, source text, questions or credentials.
        message = (
            str(exc)
            if isinstance(exc, ResearchRetrievalError)
            else "Research input failed"
        )
        print(f"ERROR: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
