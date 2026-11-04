# Step 6 evidence provenance gate — 4 November 2026

## Scope and contract reconciliation

Implemented the user's approved narrow Step 6 scope. Inspected repository
instructions, Step 5 verification, knowledge schemas, source policies, chunking,
retrieval, citations, and existing passage/retrieval/source tests before editing.

Repository searches, including hidden files while excluding dependency trees,
found no `PRD.md`, `ARCHITECTURE.md`, or `SYSTEM_DESIGN.md`. Their contents were
not assumed or replaced. Obtain them for subsequent contract reconciliation.

The gate accepts the existing `Topic`, `Iterable[RetrievedPassage]`, and validated
`SourceRegistry`. A separate internal `StrEnum` and Pydantic result follow existing
repository conventions without extending the public `AnswerStatus` or API models.
The user's Step 6 instruction approves this internal result contract.

## Files changed in this task

- `backend/app/services/evidence.py`: result contract and pure provenance gate.
- `backend/tests/test_evidence.py`: 35 synthetic, non-clinical tests.
- `docs/STEP6_VERIFICATION.md`: this implementation and verification record.

Other pre-existing working-tree changes were preserved. No routes, frontend,
production approval metadata, existing services, dependencies, or infrastructure
were changed by this task.

## Internal result contract

`assess_provenance(topic, retrieved, registry) -> EvidenceResult`

| Status | Candidates | Meaning |
| --- | --- | --- |
| `insufficient_evidence` | Empty tuple | No retrieval records were supplied |
| `invalid_evidence` | Empty tuple | The batch contains invalid evidence and is rejected in full |
| `support_assessment_required` | Nonempty tuple of `SourcePassage` snapshots | Structural and provenance checks passed; claim support remains unassessed |

These are exactly the three `EvidenceStatus` values. A result validator forbids
candidates on either rejection outcome and requires candidates on the third.
The result model is frozen and its candidate collection is a tuple. Nested
`SourcePassage` objects retain their existing mutable model contract, but are
fresh snapshots rather than aliases of input passage objects.

No outcome authorizes a medical answer. Scores and matched terms are omitted
from candidates and never used as sufficiency thresholds.

## Validation logic and reuse

1. Consume retrieval records in their supplied order, including iterators.
2. Revalidate each record through the existing `RetrievedPassage` schema with
   strict validation. This detects invalid nested fields introduced through
   mutation or unvalidated model copies, including negative, fractional, or
   boolean passage positions. Suppress serializer warnings before validation
   because such warnings can include untrusted field contents.
3. Require the requested topic to match the passage and registry topics.
4. Return `insufficient_evidence` for an empty batch, or `invalid_evidence` for
   any structural/topic failure, without partial candidates.
5. Submit every passage ID to the existing `resolve_citations()` validator.
   This reuses its fixed production eligibility policy, unknown-source checks,
   duplicate-ID rejection, source-topic checks, and deterministic ID/position
   consistency. Discard the display references; no citations are presented.
6. Convert a citation validation failure into `invalid_evidence`. Otherwise,
   return all candidate snapshots as `support_assessment_required`.

The existing production policy excludes synthetic and development-only sources
and requires clinical approval plus documented permission, license, authorization
reference, and authorization date. Synthetic sources remain excluded even with
fictional approval metadata. No gate-side development switch exists.

Retrieved positions need not be consecutive or start at zero: retrieval is a
ranked subset, unlike a complete `PassageSet`. Positions must satisfy the passage
schema and agree with `<source_id>-p<position>` identifiers.

## Tests and actual verification

Commands ran from `backend/` with the existing virtual environment.

| Command | Actual result |
| --- | --- |
| `.venv/bin/pytest tests/test_evidence.py -q` before gate implementation | Expected collection error: `assess_provenance` did not exist yet |
| `.venv/bin/pytest tests/test_evidence.py -q` after implementing the gate | First two tests passed: empty retrieval and approved-metadata synthetic rejection |
| `.venv/bin/pytest tests/test_evidence.py tests/test_passages.py tests/test_retrieval.py -q` | Final result: 206 passed in 0.36 seconds |
| `.venv/bin/pytest -q` | Final unrestricted result: 315 passed, one warning, in 1.41 seconds |
| `.venv/bin/ruff check .` | Passed |
| `.venv/bin/ruff format --check app/services/evidence.py tests/test_evidence.py` | Passed; two files already formatted |
| `git diff --check` | Passed |

The first expanded targeted test run had three new fixture-setup failures:
Pydantic refused deliberately incomplete permission records during registry
construction, before the gate ran. Corrected the test setup to explicitly bypass
registry construction for these defensive policy tests. Also corrected a new
deprecated instance-level `model_fields` lookup and formatted the new test file.
The final targeted run had no warnings or failures.

The sandboxed full-suite attempt stalled inside FastAPI TestClient and was
interrupted (exit 130), matching the environment limitation documented in Step 5.
The approved unrestricted retry passed. Its one warning is the existing upstream
Starlette/HTTPX TestClient deprecation; no dependency change was made.

Repository-wide formatting failures previously recorded in Step 5 were not
modified or reclassified as new failures. No type-check command is configured in
the existing backend `pyproject.toml`.

Coverage includes eligibility failures, missing authorization data, unknown
sources, requested/source/passage topic mismatches, invalid positions, inconsistent
IDs, duplicates, mixed batches in both orders, valid ranked subsets, high-scoring
irrelevant fictional content, and production retrieval excluding the committed
synthetic fixture. Tests also verify input preservation, candidate snapshots,
the three-value contract, and empty rejected results. Privacy tests capture
logging/stdout/stderr and forbid file opening during valid and invalid gate calls.

## Remaining limitations and next milestone

The caller must supply typed retrieval records and a validated source registry.
The gate checks registry provenance and structural consistency; it does not
independently authenticate publishers or compare passage text against original
documents. Passing provenance cannot establish relevance, completeness, medical
accuracy, or support for any proposed claim. The result remains an internal
engineering object and is not integrated with `/education/ask`.

No clinical sufficiency criteria, safety screening, model calls, medical answer
generation, or approval for real-user deployment is claimed.

The recommended next milestone is to agree a claim-to-evidence assessment
contract and synthetic acceptance cases, reconciling the missing source
specifications. Define unsupported, contradictory, and unrelated-evidence cases
before implementing that assessment. Keep API integration separate until its
preceding safety/scope screening and remaining pipeline requirements are agreed.
