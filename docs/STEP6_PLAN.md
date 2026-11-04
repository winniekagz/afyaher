# Proposed Step 6: evidence gate before generation

Status: proposal for review, not an approved product specification.

## Current state

Step 5 is implemented and its recorded verification is in
`STEP5_VERIFICATION.md`. Local deterministic keyword retrieval already exists in
`backend/app/services/retrieval.py`, with a development CLI in
`backend/scripts/search_passages.py`. Rebuilding retrieval is unnecessary.

`POST /api/v1/education/ask` remains a service-unavailable stub. Safety screening,
evidence sufficiency, generation, and medical claim-support validation are not
connected. The production source registry contains no eligible medical sources.

`PRD.md`, `ARCHITECTURE.md`, and `SYSTEM_DESIGN.md` remain missing. Obtain these
documents and reconcile them with this proposal before broader feature work.

## Smallest proposed implementation

Add an independently testable internal gate over retrieval results. It can reject
unusable evidence and report that otherwise valid candidates still require a
claim-support assessment. It must never label keyword matches sufficient to
answer a medical question.

Inputs: requested topic, retrieved passages, and validated source registry.
Production policy is fixed; there is no request-controlled development switch.

Proposed outcomes:

- `insufficient_evidence`: no retrieved passages; no candidate evidence returned.
- `invalid_evidence`: unknown, ineligible, synthetic, development-only,
  inconsistent, or duplicate passage records; reject the entire result batch.
- `support_assessment_required`: candidate records pass provenance checks, but
  no answer may be generated until a separate claim-support assessment succeeds.

The final outcome explicitly does not mean evidence is clinically sufficient.
No score threshold, passage count, or source count can establish that guarantee.
The gate does not assess symptoms, urgency, or individual health circumstances.

## Proposed files

| File | Purpose |
| --- | --- |
| `backend/app/services/evidence.py` | Small internal result type and pure gate function; reuse production eligibility and citation consistency checks |
| `backend/tests/test_evidence.py` | Synthetic unit and retrieval-to-gate regression scenarios |
| `docs/STEP6_VERIFICATION.md` | Record actual commands, outcomes, and remaining limitations after implementation |

No public request/response schema, route, frontend, dependency, database, model,
or deployment changes are proposed. The new internal result contract requires
scope confirmation under the repository's schema-change agreement.

## Acceptance tests

1. Empty retrieval returns `insufficient_evidence` with no candidate evidence.
2. A synthetic fixture is rejected even when review and permission fields are
   populated with synthetic test approval metadata.
3. Development-only real sources and real sources missing any existing
   permission or review requirement are rejected.
4. Unknown sources, inconsistent topics, inconsistent passage ID/position
   metadata, and duplicate passage IDs reject the batch.
5. One invalid item in an otherwise valid batch does not silently disappear.
6. Eligible production-scoped test metadata yields only
   `support_assessment_required`, never an answered or sufficient outcome.
7. A high lexical score for an unrelated fictional fact cannot authorize an
   answer. Use original non-clinical text only.
8. Default production retrieval over the committed synthetic fixture yields no
   evidence and the gate abstains.
9. No questions or passage text are written to logs or storage by the gate.
10. Existing API behavior, source policies, and citation regressions still pass.

All apparent approval metadata in tests is fictional; do not update actual
source approval records or place synthetic content in production source files.

## Verification commands

Run from `backend/` after implementation:

```bash
.venv/bin/pytest tests/test_evidence.py tests/test_passages.py tests/test_retrieval.py -q
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check app/services/evidence.py tests/test_evidence.py
```

These commands are proposed, not claimed as executed for Step 6. The existing
backend configuration has no type-check command. Repository-wide formatting
already has unrelated failures recorded in the Step 5 report.

## First implementation step and later boundary

After confirming this scope and reconciling available source specifications,
define the three internal outcomes and write the empty-results and synthetic
rejection tests first. Then implement the pure gate and remaining regressions.

API integration requires a separate scope that preserves validation ->
safety/scope screening -> retrieval -> evidence assessment -> generation ->
output validation ordering. Clinical sufficiency criteria and claim-support
validation must be defined and reviewed before medical answer generation.
