# AfyaHer architecture

AfyaHer is a private, local-first prototype for adults. The Next.js frontend is
presentation only. FastAPI owns validation, source policy, retrieval, and safe
failure behavior. PostgreSQL and model generation are not part of this phase.

## Knowledge retrieval

The backend keeps source metadata in `backend/data/sources/`. Curated passage
review records live separately in `backend/data/approved/passages.json`; that
file is empty until a real passage has permission and qualified review.
`backend/app/services/typesense_store.py` is the Typesense adapter. Typesense
stores passage-level records in the versioned `afyaher_knowledge_v2`
collection. The backend admin key stays server-side.

`POST /api/v1/knowledge/search` returns retrieval candidates and source
provenance. It does not generate an answer. Candidate matches have
`evidence_sufficiency: not_assessed`; no matches abstain, and infrastructure
failures return `retrieval_unavailable`. A Typesense outage never falls back to
the local keyword searcher.

Re-indexing reconciles stored approved records against the current reviewed
passage manifest, removing records that are no longer approved.

The local keyword searcher remains for isolated development fixtures and tests.
It is not a production fallback or a source of answer evidence.

## Boundaries

- Typesense does text search only. There are no embeddings or semantic search.
- A match score ranks passages; it does not establish medical claim support.
- The education endpoint remains unavailable and no LLM is connected.
- Clinical, privacy, security, and regulatory release review is still required
  before any public or patient use.
