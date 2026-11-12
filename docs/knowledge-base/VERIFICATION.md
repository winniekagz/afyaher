# Knowledge-base starter verification

Date: 2026-11-04. Scope: metadata catalogue and an optional development-only
hosted free-model selector over synthetic passages. No medical source text,
clinical approvals, public API schemas, frontend code or dependencies changed.

## Repository reconciliation

- Existing registry, eligibility, chunking, retrieval, provenance and citation
  contracts remain authoritative. FDA fits the existing metadata schema as an
  unreviewed development-only fact-sheet candidate. WHO/Monash records are unchanged.
- The hosted helper returns `list[SourcePassage]`, using existing models and
  original records, or raises `ResearchRetrievalError`. It does not create an
  evidence-gate outcome and cannot authorize an answer. It is not wired into API
  routes. Non-synthetic sources are rejected before remote transmission.
- PMC's narrative review is documented outside the registry because existing
  evidence types do not describe it accurately. No schema change was made.
- Canonical Markdown PRD, architecture and system-design documents remain absent;
  root Word drafts exist. No missing requirements were invented.

## Actual commands and outcomes

Commands below ran from `backend/`, except the final Git check.

| Command | Observed result |
| --- | --- |
| `.venv/bin/pytest tests/test_research_retrieval.py tests/test_knowledge.py tests/test_passages.py tests/test_retrieval.py tests/test_evidence.py -q` | 305 passed in 0.75s. |
| `.venv/bin/pytest -q` | Sandboxed invocation stalled and was interrupted (exit 130). Rerun outside the sandbox: **358 passed, 1 warning in 1.71s**. |
| `.venv/bin/ruff check .` | All checks passed. |
| `.venv/bin/ruff format --check .` | 34 files already formatted. |
| `.venv/bin/python -m scripts.inspect_sources` | 3 metadata-only sources; all 3 not approved for ingestion. |
| `.venv/bin/python -m scripts.search_passages_with_llm 'green lanterns'` | Lexical preview returned fixture positions 1 and 3; no LLM call. |
| `.venv/bin/python -m scripts.search_passages_with_llm --list-free-models` | Initial restricted-network attempt failed safely. Outside the sandbox, public catalogue lookup succeeded and returned 12 zero-priced `:free` variants. No credentials, queries, passages or inference were sent. This is not a live provider/model compatibility test. |
| `git diff --check` (repository root) | Passed. |

The full-suite warning is from installed FastAPI/Starlette test-client integration
deprecating `httpx` usage. No dependency was added or changed to address it.
The first focused run found one newly introduced expectation failure: an old
test assumed every registry source had production scope. It now explicitly
preserves WHO/Monash scope and checks FDA is development-only and ineligible.
There are no remaining test failures in the completed run. No frontend checks or
Docker rebuild were run for this backend/documentation task.

## Tested failure modes

Offline tests cover unknown/mixed/non-synthetic candidate batches, invalid IDs and
positions, duplicate IDs, missing configuration, malformed catalogues, nonzero or
unverified pricing, random/paid model rejection, invented selections, malformed
responses, unexpected model IDs, unverified/nonzero response cost, redirects,
network errors, response-size limits, timeout configuration, safe output and
absence of query/passage logging. CLI defaults make no provider request; live mode
requires explicit confirmation of synthetic data.

## Remaining limitations

No live model inference was executed: research credentials and a reviewed provider
were not configured. Mocked tests do not prove endpoint support, quality, privacy
or provider compliance. No medical source fetcher, source snapshot storage,
semantic relevance evaluation, claim-support assessment or medical generation was
implemented. The normal educational answer endpoint remains unavailable.

Next: review one current free model/provider combination and privately configure
the dedicated key for a synthetic-only smoke test. In parallel, obtain lawful
reuse evidence and a qualified review for one PCOS source; agree versioned source
storage before implementing real content acquisition.
