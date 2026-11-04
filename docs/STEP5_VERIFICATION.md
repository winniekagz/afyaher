# Step 5 review and verification — 4 November 2026

The working tree already contained most of this milestone. Existing work was
preserved and reused: `EmptyContentError`, multilingual splitting, the
non-whitespace content-preservation helper, `ContentScope`, `SYNTHETIC_FIXTURE`,
source policies, production citation filtering, a separate fictional Lantern
Archive fixture, and its local builder. No medical content was downloaded.

## Focused changes

- `backend/app/services/chunking.py`: reject non-integer limits, including
  booleans and fractions, with `ValueError`. Error order remains source policy,
  limit validation, then empty content. Valid-input sentence packing is retained.
- `backend/app/schemas/knowledge.py`: legacy records missing `content_scope`
  default to `development_only`. They remain readable and chunkable when otherwise
  eligible, but production retrieval requires explicitly recorded production
  scope. Passage sets now enforce their recorded `max_chars`.
- `backend/app/services/retrieval.py`: validate scope before selecting a policy.
  Previously an unknown scope, or even the string `"production"` compared by
  identity with the enum, could fall through to development permissions. Valid
  scope strings now become enums; invalid values fail explicitly.
- `backend/app/services/citations.py`: reject duplicate retrieved passage IDs and
  cited passages whose topic or deterministic ID/position conflicts with their
  source. Existing retrieved-ID, known-source, and production-policy checks remain.
- `backend/tests/test_passages.py`, `backend/tests/test_knowledge.py`, and
  `backend/tests/test_retrieval.py`: extend regression coverage for these cases.
- `README.md` and this report: document compatibility, guarantees, and results.

## How the main functions work

`chunk_text()` checks eligibility, size, and blank content before splitting.
`_sentences()` retains separators, so concatenating its units reproduces the
normalized paragraph. `_split_long()` packs those units without inserting spaces,
then splits oversized sentences at spaces or at the size limit. ASCII sentence
punctuation and ellipsis split at following whitespace; Japanese full-width
punctuation also supports adjacent sentences without spaces. Decimal text such
as `3.5` keeps its existing behavior.

`assert_valid_chunking()` removes whitespace from the input and concatenated
passages and compares the remaining characters. It also checks nonempty bounded
text, sequential positions, and deterministic IDs. This permits whitespace
normalization; it does not preserve exact document formatting. Existing seeded
randomized cases exercise mixed punctuation and Unicode whitespace too.

`can_chunk()` accepts eligible real sources or development-only synthetic
fixtures. `is_eligible_for_production_retrieval()` additionally requires production
scope and excludes synthetic fixtures regardless of approval fields.
`resolve_citations()` always uses that production policy; there is no development
citation bypass. The fixture builder validates source references and passage IDs
using the existing models and writes explicitly development-only JSON.

## Executed checks

Commands ran from `backend/`, using the existing locked virtual environment.
No dependencies were added and no type-check command is configured in
`pyproject.toml`.

| Command | Actual result |
| --- | --- |
| `.venv/bin/pytest tests/test_passages.py -q` (before edits) | 102 passed |
| `.venv/bin/pytest tests/test_passages.py -q` (Phase 1 completed) | 120 passed |
| `.venv/bin/ruff check app/services/chunking.py tests/test_passages.py` | Passed before Phase 2 |
| `.venv/bin/ruff format --check app/services/chunking.py tests/test_passages.py` | Passed before Phase 2 |
| `.venv/bin/pytest tests/test_passages.py tests/test_knowledge.py tests/test_retrieval.py -q` | 231 passed |
| `.venv/bin/pytest -q` | 280 passed, one upstream Starlette/HTTPX deprecation warning |
| `.venv/bin/ruff check .` | Passed |
| `.venv/bin/ruff format --check .` | Failed: existing formatting in `app/api/v1/education.py`, `tests/test_education.py`, and the newly edited retrieval test; formatted the retrieval test only |
| `.venv/bin/ruff format --check app/services/chunking.py app/services/citations.py app/services/retrieval.py app/schemas/knowledge.py tests/test_knowledge.py tests/test_passages.py tests/test_retrieval.py` | Passed: all seven changed Python files |
| `.venv/bin/python -m scripts.build_passages --out-dir /tmp/afyaher-step5-passages` | Built five passages from one synthetic source; sizes 211, 268, 224, 236, 166 characters |

The initial full test attempt stalled inside sandboxed FastAPI TestClient and was
interrupted. The approved unrestricted retry produced the 280-test passing result.
A new punctuation test initially expected separate chunks although both sentences
fit; its limit was corrected before the successful Phase 1 run.

## Limits and next step

No frontend, public request contract, routes, database, embedding, LLM,
authentication, or deployment changes were made. Existing unrelated working-tree
changes remain. No source has gained clinical approval or ingestion permission.
Citation traceability does not demonstrate medical claim-to-evidence consistency.
Production medical use still requires that validation and qualified review.

`docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/SYSTEM_DESIGN.md` remain absent;
obtain them before broader feature work. The next smallest task is to reconcile
those specifications and agree evidence-sufficiency and claim-support acceptance
tests before implementing answer generation.
