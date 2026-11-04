"""Export current FastAPI documentation without starting a server or calling APIs.

From backend/: uv run python -m scripts.export_openapi
"""

import argparse
import json
from pathlib import Path

from app.core.config import Settings
from app.main import create_app

DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    # Documentation export must not depend on a developer's local .env file.
    app = create_app(Settings(_env_file=None, cors_origins=[]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Exported OpenAPI documentation to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
