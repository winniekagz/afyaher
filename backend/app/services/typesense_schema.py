"""Versioned Typesense collection definition for curated knowledge passages."""

COLLECTION_SCHEMA_VERSION = "v2"


def collection_schema(name: str) -> dict[str, object]:
    """Return a reproducible schema; text search is only over passage content."""
    return {
        "name": name,
        "fields": [
            {"name": "topic", "type": "string", "facet": True},
            {"name": "source_id", "type": "string", "facet": True},
            {"name": "source_title", "type": "string", "index": False},
            {"name": "source_url", "type": "string", "index": False},
            {"name": "section", "type": "string", "index": False},
            {"name": "passage", "type": "string"},
            {
                "name": "publication_date",
                "type": "int64",
                "optional": True,
                "index": False,
            },
            {"name": "approved_at", "type": "int64"},
            {"name": "approval_status", "type": "string", "facet": True},
            {"name": "content_hash", "type": "string", "index": False},
        ],
        "default_sorting_field": "approved_at",
    }
