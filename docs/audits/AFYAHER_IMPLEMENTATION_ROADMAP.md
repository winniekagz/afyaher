# AfyaHer implementation roadmap

Date: 4 November 2026. Proposed sequence for review, not implementation approval.
See [current state](AFYAHER_CURRENT_STATE_AUDIT.md) for verified baselines and
[gap IDs](AFYAHER_GAP_ANALYSIS.md) for traceable requirements.

Preserve the current UI and working keyword retrieval. Keep the medical-answer
endpoint unavailable until the entire safety/evidence/output path is ready.
Milestones may progress independently where dependencies allow; none permits a
public release on its own. Complexity: S = focused local change; M = several
related components/contracts; L = cross-cutting integration plus evaluation.

## Milestone dependencies and deliverables

| ID / priority / size | Goal and why | Dependencies | Files/components affected (proposed) | Acceptance criteria and required tests | Clinical/legal review |
| --- | --- | --- | --- | --- | --- |
| M0 — P1, S | Reconcile authoritative specifications and pilot scope; remove ambiguity (G01,G20) | Audit review; obtain missing system-design document or explicit authority to draft it | Root Word specs, canonical `docs/PRD.md`/`ARCHITECTURE.md`/`SYSTEM_DESIGN.md` if approved, status-document references; do not silently replace source docs | Decide pages-only vs assistant pilot, UI limits, HTTP-200 unavailable semantics, JSON-now/DB-later, hosted vs local model decision; explicit requirement/owner/status matrix. Documentation consistency checks; no invented sign-offs | Product/engineering review now; clinical/privacy/legal owners must review applicable release requirements |
| M1 — P1, M — recommended next | Strict and truthful frontend→unavailable-backend slice; prove API trust boundary without generation (G09–G10,G15) | Existing route/schema; audit and narrow scope approval. Can proceed while M0 document collection continues because public schema stays unchanged | `frontend/lib/api.ts`, `lib/services/assistant.ts`, `components/assistant/assistant-panel.tsx`, corresponding unit tests and `e2e/learning.spec.ts` | Reject malformed/topic-mismatched payloads; preserve unavailable status/limitation/disclaimer; identify API vs fixed demo; test synthetic POST, 422/network/timeout and retry. Unit, lint, type, build, browser when available | Engineering; no clinical approval claimed. Any revised medical wording goes through clinical review |
| M2 — P0 before real input, M | Protect question/error/privacy boundary and private demo access (G06–G07,G23) | M0 decisions on echo/retention/access and response errors; schema changes explicitly approved | `backend/app/main.py`, `api/v1/education.py`, `core/config.py`, relevant schemas only if approved, backend tests, frontend failure handling, deployment docs/config | No raw input in sanitized 422/error/log output; no-store on question/error responses; agreed request-byte and rate limits; private access control verified. Synthetic log/error capture, boundary-size, CORS, repeated-request and cache-header tests; no raw-question telemetry | Privacy/security review required before external input; legal review defines applicable obligations, not inferred in code |
| M3 — P0 before generation, M | Independent safety/scope policy with conservative interruption (G02) | M0 taxonomy and clinical reviewer; M2 privacy-safe testing | Proposed `backend/app/services/safety.py`, internal policy/result contracts and tests, reviewed policy documentation | Urgent/scope/uncertain outcomes short-circuit retrieval/generation; no diagnosis, treatment/dosing advice or reassurance from a non-match. Clinician-reviewed synthetic positive/negative/paraphrase/adversarial cases; never claim reliable emergency triage | Clinical review required for medical cases/rules/messages; privacy review of evaluation data |
| M4 — P0 before real ingestion, M | Immutable source revisions and approval governance (G04–G05,G08,G12) | M0 decisions; actual reviewer/permission process. No database prerequisite | `backend/app/schemas/knowledge.py`, knowledge/chunking/citation/retrieval/gate contracts and tests; source approval/revision ADR; editorial metadata boundary | Changed content/version or chunk recipe cannot silently reuse citation identity; stale/tampered passage rejected; permission/review evidence and revocation/re-review recorded; synthetic isolation unchanged. Mutation, stale-version, re-chunk, policy and citation regressions | Clinical approval process and permission/licensing review required; schema changes need explicit approval |
| M5 — P0 before medical generation, M | Claim-support contract and independent evaluator (G03) | M0 assessment criteria; M4 revision identity for real evidence. Non-clinical contract/tests may start earlier | Proposed `backend/app/services/claim_support.py`, internal contracts, synthetic evaluation corpus/tests, reviewer-facing assessment specification | Distinguish supported, unsupported, contradictory and uncertain/missing evidence; no passage-count/score sufficiency shortcut; no support inferred from valid citation IDs. Original fictional claim/passage test pairs first; then clinically reviewed medical evaluation, with unresolved results abstaining | Clinical review required for medical validity/acceptance; no LLM or new dependency implicitly approved |
| M6 — P2 conditional, M | Minimal source/passage DB persistence, if storage need is confirmed (G21) | Explicit architecture/dependency/schema approval; M4; M0 reconciles optional DB wording | Future `backend/app/models/`, repository layer, approved Alembic migrations, settings/Compose and DB tests | Persist sources, immutable revisions, passages and approval metadata with constraints/least privilege; deterministic query/parity with JSON adapter; transactional load and rollback tested in disposable DB. No chat/question tables or embeddings | Permission/privacy review of stored corpus and access; no clinical approval implied by persistence |
| M7 — P1, M | Controlled approved-content ingestion and editorial reconciliation (G04,G08,G12,G17) | M4, actual lawful authorization and qualified review; M6 only if DB chosen | Explicit import script/service, authorized source artifacts, reviewed summaries/source metadata, container artifact packaging, ingestion tests | One approved PCOS source revision enters controlled pipeline; unsupported permissions/revoked revisions rejected; reproducible passage IDs/source mapping; reviewed UI reference context agrees with backend. Synthetic tests first; actual source content only after permission/review approval | Clinical and licensing review required; do not mark publisher authority as AfyaHer approval |
| M8 — P1, L | Integrate a generation-disabled backend pipeline, then controlled generation/output checks in a separately approved increment (G13) | M2,M3,M4,M5; M7 for medical data. Hosted provider/dependency/cost authorization before any call | Thin education route, backend orchestration service, retrieval/gate/support/output components, private settings and API integration tests | First increment proves validation→screen→retrieve→provenance→assessment short circuits with no generator. Later reviewed increment bounds provider timeouts/retries, validates every citation/claim/output, returns limitation on any failure; never falls back to unsupported medical answers. Dependency-failure and injection/adversarial tests | Clinical/privacy/security review required before medical trials; provider/legal review before data transfer |
| M9 — P3 conditional, M/L | Embedding/semantic/hybrid experiment only if measured retrieval failures justify it (G22) | Keyword evaluation baseline; separate resource/model/dependency approval; M4 for revision linkage; M6 only if vector DB selected | Retrieval adapter and evaluation scripts; optional approved embedding provider/local model and storage | Compare held-out retrieval relevance/recall, irrelevant returns, latency/resource/cost against existing keyword baseline; retain eligibility and provenance isolation; no medical answer authorization from better similarity | Clinical review for medical evaluation corpus; licensing/privacy/provider review as applicable |
| M10 — P0 release gate, L | Reviewed private MVP validation and any later restricted external pilot (G02–G08,G16,G23) | All applicable earlier gates, reviewed content, browser checks, incident/rollback path; product chooses pages-only vs assistant scope | Evaluation corpus/report, accessible UI fixes, release checklist, deployment/access controls and operations docs | Demonstrate all intended journeys on mobile/keyboard/low-bandwidth baseline; consented non-sensitive research, measured proposed PRD targets, approved release decision, rollback drill. No fabricated claims of ≥80% completion or clinical efficacy | Qualified clinical, privacy/legal and security release review required; assistant remains disabled if its gates are unmet |

## Parallel quality track

Q1 (P2, S/M) restores a matching Playwright Chromium revision, reruns all 16 cases,
and adds API-path assertions with M1. It depends on approved environment setup,
not on LLM/database work. Current failure is launch infrastructure, not established
UI regression. Avoid downloading tools within an audit without the required
approval. Files: browser setup documentation, package/test configuration only if
necessary, `frontend/e2e/`; acceptance: clean mobile/desktop suite plus keyboard
and tablet checks, recording any actual assertion defects. No clinical review
needed for synthetic engineering scenarios.

Q2 (P2, S/M) adds CI using existing locked pytest/Vitest/lint/type/build checks,
repairs existing formatting in a focused change, and introduces approved dependency
scanning. Files: `.github/workflows/`, existing test/setup docs and only the
identified formatting files. Acceptance: reproducible CI failures for deliberate
invalid test inputs, secrets never printed, no real health fixtures. Any new tool
needs approval; backend type tooling is a later explicit choice.

Q3 (P2, M) measures accessibility/readability, performance and low-bandwidth
behavior using the current design. Files: demonstrated CSS/component defects and
evaluation reports only. Acceptance: documented keyboard/screen-reader/reflow/
zoom/contrast checks, agreed measured performance budgets and verified fixes;
no redesign. Product accessibility review required; review medical copy separately.

## Recommended dependency order

M0 establishes authority and review owners. M1 plus Q1 repairs an already connected
engineering boundary; M2 closes privacy/access blockers before any real input.
M3 and M4 can proceed as separate reviewed contracts, with M5 non-clinical
evaluation work alongside them. M6 is conditional, not a reason to delay safety
or force a vector database. M7 requires actual permission and clinical review.
M8 first integrates disabled/abstaining behavior, then considers controlled
generation only after its gates. M9 is optional measured optimization, not an
MVP prerequisite. M10 remains the release decision, never an automatic consequence
of passing technical tests.

## Product decisions requiring answers

1. Are the supplied version-0.1 drafts the canonical basis for reconciliation,
   and where is the system-design document? Do not treat their draft ADRs as
   independent approval to change stack/dependencies.
2. Is the first external pilot reviewed education pages only with assistant
   disabled, or is medical answering a later pilot? Who owns release approval?
3. Who is the qualified clinical reviewer, what evidence records approval, and
   what is the re-review/revocation cadence? Who verifies reuse permissions?
4. Should typed input use the PRD's 2,000-character cap or an explicitly approved
   narrower UI cap? Is echoing questions necessary? What retention/access notice
   and privacy review apply to the API path?
5. Is JSON sufficient for the next milestone, with PostgreSQL deferred as the
   Word architecture suggests? If local models are considered, resolve the
   difference from the hosted-API target before tooling or cost commitments.
6. What measured usability/accessibility/performance/evidence targets will count
   as passed, and who reviews their evaluation? PRD examples are proposals.

No answer to these questions is inferred by this audit. The
[next milestone](AFYAHER_NEXT_MILESTONE.md) is deliberately limited to an existing
unavailable API contract and does not depend on deciding clinical thresholds.
