# AfyaHer current-state audit

Audit date: 4 November 2026. Scope: current working tree, including existing
uncommitted work. Documentation only; no application implementation or migration.

## Assessment

AfyaHer is a private engineering prototype with a substantial responsive UI,
working health and educational-request contracts, and independently tested local
knowledge components. It is not an integrated medical-answer system. Step 6 is
implemented. Production medical source eligibility is currently empty. No
application database, embeddings, or model integration exists.

Current verification: 315 backend tests and 37 frontend tests pass; lint and
frontend type checking pass; the production frontend builds. Browser tests cannot
launch the required Chromium revision. Existing formatting failures remain.
These findings do not establish clinical safety, legal clearance, or WCAG conformance.

Related deliverables: [gap analysis](AFYAHER_GAP_ANALYSIS.md),
[roadmap](AFYAHER_IMPLEMENTATION_ROADMAP.md), and
[next milestone](AFYAHER_NEXT_MILESTONE.md).

## Specifications, precedence, and reconciliation

Read the root [PRD](../../AfyaHer_PRD.docx) and
[architecture](../../AfyaHer_Architecture.docx) using Python's standard-library
ZIP/XML support. Both are version 0.1, dated 4 November 2026, explicitly drafts
for product, engineering, and clinical review. Their reported implementation
status was checked against code rather than accepted as fact. Embedded document
text was treated as specification material, not executable agent instructions.

Also read [AGENTS.md](../../AGENTS.md), [CLAUDE.md](../../CLAUDE.md),
[frontend instructions](../../frontend/AGENTS.md),
[Step 5](../STEP5_VERIFICATION.md), [Step 6](../STEP6_VERIFICATION.md),
the existing Day 1, frontend UX, implementation-status documents, and README.
Architecture §6 contains proposed ADR-01 through ADR-07; no separate ADR directory
was found.

No `PRD.md`, `ARCHITECTURE.md`, `SYSTEM_DESIGN.md`, or
`AfyaHer_System_Design.docx` was found in the repository, including a hidden-file
search excluding dependency/build trees. The Word PRD and architecture are now
available; the system-design specification remains unavailable. Please provide
that document. This audit does not manufacture it or mark either draft approved.

| Specification | Requirement / decision | Verified disposition |
| --- | --- | --- |
| PRD §§1–3 | Adults 18+, Kenya first, English, mobile web; understand sources and prepare for clinicians | Three-topic UI, English document language, notices and topic navigation exist; audience notice is not age verification |
| PRD §4 US-01, US-02 | Three entry journeys and browsable condition pages | Present; static editorial content, no clinical approval |
| PRD §4 US-03 | Supported topic, 3+ non-whitespace characters, 2,000 after trimming, safe unavailable response | Backend matches; textarea/demo cap is 500 and submit accepts one character; API unavailable status is replaced by a demo limitation |
| PRD §4 US-04; §6 | Known retrieved passage citations, independent claim support | Backend mapping and provenance gate exist; UI examples link static references and bypass these backend components; no claim-support assessor |
| PRD §4 US-05 | Editable general appointment prompts | Functional in-memory editor and clipboard path; no recommendations inferred from user data |
| PRD §4 US-06; §§6,9 | Clinically reviewed escalation, no ordinary generation for urgent/uncertain cases | Static notices exist; no input safety/scope service; no normal generation exists either |
| PRD §7 | WCAG 2.2 AA target, performance baseline, privacy, security, operational metrics | Partial technical foundations; no completed accessibility audit, measured performance budgets, rate control, dependency-scanning CI, or metrics pipeline |
| PRD §3 | Proposed 5–10 research sessions, ≥80% task completion, citation/isolation evaluation targets | Proposals only. No research results or complete clinical/evidence evaluation supplied; unit isolation tests pass |
| Architecture §§3,6 ADR-02–06 | FastAPI orchestration, keep keyword retrieval, distinct provenance/claim support, unavailable route until reviewed | Logical boundaries preserved; knowledge services are standalone and not wired to the route; Step 6 has advanced beyond the drafts' reported state |
| Architecture §§5–6 ADR-07 | Files now; optional later PostgreSQL/pgvector | Matches implementation. AGENTS/CLAUDE describe PostgreSQL/pgvector and hosted APIs as the approved target; optional DB wording and local-model option need explicit future reconciliation |
| Architecture §7 | Source revisions must not silently reuse passage IDs | Not implemented: deterministic IDs use source ID plus position only; no content fingerprint/version |
| PRD §§5,10 | Accounts/bookmarks later; no diagnoses, prescriptions, chat history, payments, or unreviewed public answers | Deferred/absent as intended; no evidence justifies adding them now |

The documents use `/education/ask` in a logical diagram; the actual versioned
route is `/api/v1/education/ask`. Use the latter for integrations. The drafts do
not supply a full system-design/OpenAPI failure contract. Names such as
`EvidenceGateResult` and `RetrievalResult` are conceptual; actual code uses
`EvidenceResult` and `RetrievedPassage`, which is compatible rather than a defect.

Historical documents are not live state: `docs/IMPLEMENTATION_STATUS.md` reports
the education endpoint missing; `docs/FRONTEND_UX.md` reports no question API
adapter; README describes typed input as local and its Git section describes an
empty root repository. Current code includes the adapter and stub, and root
`git log -1` returns `6476926`. The nested frontend repository also exists
(`84d19e9` at inspection). No history or Git layout was changed.

## Frontend architecture and design

Evidence: [app layout](../../frontend/app/layout.tsx),
[shell](../../frontend/components/layout/shell.tsx),
[provider](../../frontend/components/layout/prototype-provider.tsx),
[navigation](../../frontend/components/navigation/navigation.tsx),
[styles](../../frontend/app/globals.css),
[primitives](../../frontend/components/ui/primitives.tsx),
[API client](../../frontend/lib/api.ts),
[assistant service](../../frontend/lib/services/assistant.ts),
[TypeScript configuration](../../frontend/tsconfig.json).

Next.js App Router uses server pages for content and route resolution, with client
components for navigation/search/forms/conversation. Dynamic params and search
params are awaited. Known conditions have static params; unknown condition/source
IDs call `notFound()`. Shared shell supplies a skip link, focused main landmark,
navigation, footer, and an in-memory React provider. Strict TypeScript is enabled.
No Next.js domain API route or database logic was found.

The provider holds topic-specific messages, appointment drafts, and request states.
It survives client navigation and clears on reload; no browser storage is used in
these components. Backend calls live in `lib/api.ts`; `apiAssistant` maps them to
UI answers. Runtime health validation is strong; education response checking is
only partial and ends with a type assertion.

Retain the brand: mauve `#c599b6`, rose `#e6b2ba`, peach `#fad0c4`, cream `#fff7f3`,
plum `#382536`, with darker functional colors. Georgia headings/system sans body,
shared buttons/cards/notices, responsive grids at 1000/760px, reduced-motion rules,
visible focus, labeled controls, native disclosures, and many ≥44px controls are
implemented. CSS also has 0.53–0.69rem ancillary text; readable sizing/zoom needs
measurement. This is a targeted usability concern, not evidence for a redesign
or a demonstrated WCAG failure. No new visual inspection or screen-reader test
could be completed because the standard browser launch is blocked.

### Screen and journey inventory

| Screen / relevant files | Implemented and functional | Static, incomplete, broken, or missing; accessibility/usability |
| --- | --- | --- |
| Homepage: `frontend/app/page.tsx`, `components/conditions/topic-search.tsx`, `condition-card.tsx` | Three journeys, topic cards, query filtering and no-results/reset, education/privacy notices | All editorial content is static; no search backend or accounts needed by MVP. Labeled search and decorative aria-hidden artwork exist; no fresh rendered layout verification |
| Library: `app/conditions/page.tsx`, `components/conditions/topic-search.tsx` | Three-topic filtering, result-count live status, clear/reset empty state | Local metadata only, not curated live catalog; matches initial scope |
| Details: `app/conditions/[slug]/page.tsx`, `components/education/condition-article.tsx` | Overview/meaning/assessment, native FAQ, anchor navigation, source and appointment links; unknown slug 404 | Fixed, unreviewed summaries. Publisher links are not retrieved-passage citations. Torsion notice is static; clinical approval, version identity, and content lifecycle missing |
| Ask: `app/ask/page.tsx`, `components/assistant/assistant-panel.tsx`, `lib/services/assistant.ts` | Topic picker, local fixed examples, API-backed arbitrary submit, spinner, generic error/retry, source links, clear conversation, static urgency notice | Whole panel says Demo; typed text goes to API; unavailable result is replaced by demo limitation. 500 UI vs 2,000 API cap; no frontend minimum of three. No abort on unmount in this call path; API source metadata discarded; disclaimer retained by adapter but not rendered from the response. API/safety behavior incomplete; examples are not clinical review evidence |
| Appointment: `app/appointment/page.tsx`, `components/appointment/appointment-editor.tsx` | Edit/remove/add up to 15 prompts, 300-char controls, empty state, clipboard success/failure live status, per-topic memory | No persistence or export beyond explicit clipboard; intentional. Torsion notice present for that topic. Human-written prompts remain unreviewed; browser clipboard/keyboard path not freshly verified |
| Source details: `app/sources/[sourceId]/page.tsx`, `lib/content/conditions.ts` | Publisher URL/date/context, unreviewed status, external-link notice, topic-aware return links; unknown ID 404 | Separate static registry from backend. NHS/BMJ IDs absent from backend registry; Monash absent from frontend. Source revision, authorization evidence, and a real retrieved passage cannot be inspected here |
| Mobile/global navigation: `components/navigation/navigation.tsx`, `components/ui/topic-picker.tsx`, `app/globals.css` | Bottom Explore/Ask nav, desktop appointment link, topic retained through conditions/query; `aria-current`, Suspense fallback | Bookmarks correctly absent. Two-item mobile nav relies on other paths for appointment access. Browser/tablet/320px reflow and keyboard checks exist but were launch-blocked in this audit |
| Developer status: `app/dev/status/page.tsx`, `lib/api.ts` | Real health GET, five-second timeout, cancel on unmount, loading/error/retry, local-only audience notice | Liveness only; no evidence/DB readiness. Retain as a developer tool rather than presenting connectivity as clinical or pipeline readiness |
| Shared failures: `app/loading.tsx`, `app/error.tsx`, `app/not-found.tsx` | Loading status, retry boundary, library recovery link | Generic error copy says no AI service was used; true for current no-LLM implementation, must be revisited before any future model integration |

### Assistant data flow and trust

Suggested question → `demoAssistant` → fixed `conditions.ts` paragraph and static
source ID. Typed question → `apiAssistant` → HTTP POST → backend unavailable stub
→ panel replaces unavailable answer with demo limitation. Network failures yield
error/retry, not that fallback. The panel verifies source IDs against the static
frontend list; it cannot display new backend sources without coordinated changes.
The demo does not run retrieval, source eligibility, claim support, or a model.

The static urgency notice appears on the Ask page before the panel, with explicit
no-rule-out wording. It is not input screening. A stored API `urgent_guidance`
answer can render special copy, but the backend currently never emits one. No
diagnosis or medication advice generator exists.

## Backend/API implementation

Evidence: [main](../../backend/app/main.py), [settings](../../backend/app/core/config.py),
[health route](../../backend/app/api/v1/health.py),
[education route](../../backend/app/api/v1/education.py),
[education schemas](../../backend/app/schemas/educational.py),
[tests](../../backend/tests/test_education.py).

`create_app(Settings)` installs CORS and two versioned routers. Settings read local
`.env`; examples contain origins only. Explicit default loopback origins on ports
3000/3001, GET/POST, Content-Type, no credentials; preview/dev Compose overrides
use their own exact local origins. CORS is not access control.

| Contract | Actual behavior |
| --- | --- |
| `GET /api/v1/health` | 200 `{status: "ok", service: "afyaher-api"}`, `Cache-Control: no-store`; no readiness checks |
| `POST /api/v1/education/ask` | Accepts only topic and question; three topics, string-only, trim, ≥3 non-whitespace and ≤2,000 normalized characters; extra fields forbidden |
| Successful valid POST | HTTP 200 with application status `service_unavailable`, echoed normalized topic/question, fixed unavailable answer, empty sources, limitation, exact medical disclaimer |
| Invalid POST | Framework HTTP 422 with detail array; default validation errors include input values; no custom safe-error handler |
| Unsupported methods | 405; CORS tests exercise allowed and rejected origins/preflight |

`service_unavailable` is an application outcome at HTTP 200, not HTTP 503. This
is covered by tests; do not silently change transport semantics during integration.
Pydantic response schemas validate types but do not enforce future semantic rules
such as nonempty supporting citations on `answered`.

No safety service, rate/body-byte limiter, request authentication, privacy error
sanitizer, metrics middleware, or generation orchestration is registered. Routes
contain no raw-question logger or storage. Uvicorn access logging is enabled by
its ordinary runtime invocation; application code alone does not establish
reverse-proxy, developer-tool, provider, or error-report retention behavior.
The education response lacks explicit no-store protection despite echoing input.

## Database and persistence: explicit answers

Evidence: [backend dependencies](../../backend/pyproject.toml),
[Compose](../../compose.yaml), [dev](../../compose.dev.yaml),
[preview](../../compose.preview.yaml), [backend image](../../backend/Dockerfile),
[knowledge models](../../backend/app/schemas/knowledge.py),
[data directory](../../backend/data).

| Question | Answer and status |
| --- | --- |
| 1. Working application database? | No repository implementation or application DB wiring found. This is not an inventory of unrelated databases installed on the host |
| 2. PostgreSQL configured? | Missing from application settings, environment example and all Compose files; planned target only |
| 3. Migrations? | Missing: no Alembic dependency, configuration, or migrations |
| 4. Sources persisted where? | Implemented JSON metadata: `data/sources/pcos.json` and separate synthetic registry |
| 5. Passages persisted? | Implemented local synthetic JSON: `data/fixtures/synthetic/passages/synthetic-lantern-archive.json`; no production passage store or DB |
| 6. Embeddings? | Missing: no stored vectors, models, provider adapter, or embedding fields |
| 7. pgvector? | Planned only; no extension, image, DDL, or vector index configured |
| 8. Real ingestion? | No medical acquisition/approval/import pipeline. Only a controlled local synthetic text-to-passages builder exists |
| 9. Schema/migration inconsistencies? | No DB migrations exist to drift. Pydantic schemas are active; version/fingerprint and clinical reviewer/audit identity are absent relative to Architecture §7. Future ORM mappings need reconciliation, not repair of a fictitious current DB |
| 10. Smallest DB milestone? | After revision/provenance and approval contracts are agreed, persist source revisions and passages only, with reviewed Alembic migration and parity tests against JSON retrieval; no chat/question storage or vectors initially |

Compose configuration validates. Its base project status query showed only
`afyaher-backend-1`, exited with code 255; it does not prove any current deployment
healthy. Preview/dev stack runtime was not verified. No containers were rebuilt,
started, or stopped for this audit. Playwright launched its own temporary test
servers, then completed/cleaned up its run. Backend image copies `app/` only,
so current knowledge data and scripts are not packaged for a future live pipeline.
This does not break the current health/unavailable routes, which do not load them.

## Knowledge and RAG inventory

| Component / entry point | Behavior, safety controls, tests | Limitation / readiness |
| --- | --- | --- |
| `schemas/knowledge.py`, `services/knowledge.py::load_registry` | Typed IDs/topics/enums; unknown keys and duplicates rejected, registry topics consistent; required unknown provenance fields explicitly null; `test_knowledge.py` | Dates are metadata, not version identity; no reviewer identity/review evidence, refresh/revocation lifecycle, or publisher authenticity check |
| `can_chunk`, `is_eligible_for_production_retrieval` | Distinct policies; real content needs permission, license/authorization/date and approved review; production additionally explicit scope and non-synthetic type; policy regressions in `test_passages.py` | Production registry has two metadata-only PCOS sources, neither eligible. `is_eligible_for_ingestion` alone does not exclude synthetic types; production uses the stronger policy |
| `chunking.py::chunk_text` | Eligibility → integer limit → explicit empty failure; Unicode whitespace normalization, ASCII/ellipsis and adjacent CJK sentence boundaries, hard splitting; deterministic IDs and preservation helper; `TestChunking` | Non-whitespace preservation, not exact formatting; IDs stable only for fixed source content/chunk settings, not immutable source revisions |
| `scripts/build_passages.py`, synthetic fixtures | Synthetic-only source check, validated passage set/source refs/positions/size; local JSON output; builder tests in `test_passages.py` | No licensed medical ingestion; writer may overwrite output for same source ID; only for synthetic local use |
| `retrieval.py::retrieve`, `scripts/search_passages.py` | Deterministic lexical ranking; production default; invalid scopes rejected; stopword filtering and CJK bigrams; bounded query/limit and consistency checks; `test_retrieval.py` | Not semantic relevance, completeness, clinical evidence sufficiency, or support assessment. Keep until a measured retrieval gap justifies additions |
| `evidence.py::assess_provenance` | Step 6 complete: strict retrieval-record revalidation; topic consistency; delegates all IDs to production citation checks; absent/invalid batches empty; valid candidates still require support; 35 tests in `test_evidence.py` | Trusted validated registry; no original-source text authentication or immutable revision; nested candidate models remain mutable. No medical sufficiency decision and no API integration |
| `citations.py::resolve_citations` | Cited ID must be retrieved; rejects unknown/ineligible sources, duplicate IDs, topic and canonical ID/position mismatches; metadata from registry; `TestCitations`, `TestSyntheticCitations`, retrieval integration tests | Maps to source-level display references; no quote/offset/version or claim-to-evidence check. Static frontend citations do not traverse this function |

Readiness dependencies: approved medical ingestion needs actual permission,
qualified review, version identity and audit records first. Local embeddings need
separate architecture/dependency/resource approval and a non-clinical evaluation
corpus; no immediate dependency on DB or medical content. Vector search additionally
needs persistence decisions and measured retrieval benefit. Hybrid retrieval should
preserve keyword behavior and prove benefit on a held-out corpus. Claim-support
validation needs an explicit supported/unsupported/contradictory/uncertain contract
and reviewed evaluation cases. Generation remains blocked until source governance,
safety/scope, claim-support and output checks are validated. None of these later
steps is authorized by this audit.

## Safety and privacy controls

| State | Controls / evidence |
| --- | --- |
| Implemented technical | Unavailable backend; no model call; scoped source policy, synthetic exclusion, citation/provenance rejection; typed request limits; explicit notices; no account/chat DB/browser storage; synthetic tests; loopback Compose ports; non-root containers; ignored local secret files |
| Proposed/missing technical | Input safety/scope interruption, claim-support and output validation, request byte/rate limits, sanitized 422 responses, explicit question-response no-store, outcome-only telemetry, content revision/audit integrity, live incident/rollback mechanism |
| Requires clinical review | Urgency wording/rules and examples, scope taxonomy, static condition summaries and appointment prompts, clinical approval identity/evidence, medical claim evaluation and re-review cadence |
| Requires privacy/legal/security review | Content licensing/authorization, external pilot boundaries, applicable Kenyan obligations, data-flow and retention/deletion notices, analytics/provider arrangements, administrative access and incident handling |

No legal compliance determination or medical-content correctness validation was
performed. Static publisher statements/dates were audited as stored metadata,
not externally reverified as current guidance. Disclaimers, noindex metadata and
CORS cannot substitute for controlled access or qualified review.

## Fresh verification ledger

Commands below were executed during this audit, not inferred from prior reports.
Backend commands run in `backend/`, frontend commands in `frontend/`, Docker/Git
commands at root. No package installs, paid calls, migrations or content downloads.

| Command | Actual result and qualification |
| --- | --- |
| `.venv/bin/pytest -q` | 315 passed, one pre-existing Starlette/HTTPX deprecation warning, 1.11s; unrestricted run due established sandbox TestClient limitation |
| `.venv/bin/ruff check .` | Passed |
| `.venv/bin/ruff format --check .` | Failed: `app/api/v1/education.py`, `tests/test_education.py`; both already recorded in Step 5 |
| `npm run test` | 37 passed across seven files; includes 17 API-boundary, 8 service, 3 panel tests |
| `npm run lint` | Passed |
| `npm run typecheck` | Passed: route type generation and `tsc --noEmit` |
| `npm run format:check` | Failed: `lib/services/assistant.ts`, `tests/api.test.ts`, `tests/assistant-service.test.ts`; newly observed audit findings in pre-existing user changes |
| `npm run build` | Sandbox attempt failed parsing TypeScript `--showConfig`; unrestricted retry passed compilation, type checking and static/dynamic route build |
| `npm run test:e2e` | First attempt blocked before tests by read-only uv cache lock |
| `UV_CACHE_DIR=/tmp/afyaher-uv-cache npm run test:e2e` | Unrestricted retry started local servers; all 16 cases failed at browser launch: required `chromium_headless_shell-1248` absent (installed revision is 1234). No application assertions verified |
| `docker compose config --quiet` | Passed |
| `docker compose ps --all --format json` | Sandbox denied socket; unrestricted read succeeded: base backend container exited 255; no current healthy base stack demonstrated |
| `git status --short`; `git -C frontend status --short`; `git log -1`; `git -C frontend log -1` | Inspected existing root and nested histories/user changes; no Git mutations |

No CI workflow files were found under `.github/workflows`; `.github` contains
Copilot instructions. Backend has no configured type checker. Frontend browser
cases cover health/timeout, topic navigation, PCOS-source-appointment journey,
clipboard, no browser persistence, urgent notices, tablet overflow and skip-link
keyboard access. They do not currently assert that typed questions are sent to
the backend or that unavailable outcomes remain visible. Unit panel tests mock
the demo path rather than the new API path.

Additional read-only synthetic probes confirmed:

1. `askEducationalQuestion()` accepted `{status: "answered", topic:
   "unsupported-topic", question: 123, answer: 42, sources: [{}], disclaimer: null}`.
   Reproduced by transpiling `lib/api.ts` in memory with the installed TypeScript
   compiler, injecting a fake `fetch`, and invoking the exported function. This
   establishes weak runtime validation, not a real backend malformed response.
2. In-process `TestClient(create_app())`: valid synthetic POST returned HTTP 200,
   `service_unavailable`, and no Cache-Control header. Invalid synthetic POST
   returned 422 with `input` fields. No real health text was used or printed.
3. `chunk_text()` on two different fictional sentences under the same eligible
   fictional source reused the same passage ID. This confirms Architecture §7's
   revision requirement is unmet. No registry or passage output was written.

The initial sandboxed asynchronous API probe stalled and was interrupted; its
unrestricted TestClient retry produced observations 2–3. Probes used `node -`
and `.venv/bin/python -` heredocs, reading existing modules only. Raw synthetic
question/passage text was omitted from probe output. Test/build generated caches
and ignored test artifacts may change; application source changes are outside
this audit. Existing six-file frontend modifications were preserved.

## Release conclusion

The UI foundation is worth preserving and the backend components are useful
tested building blocks. An available medical-answer product is not implemented.
Keep the assistant unavailable/private and use synthetic scenarios. Before any
external use, settle the education-pages-only versus assistant pilot decision,
obtain qualified review and permissions, define privacy/security release gates,
repair boundary correctness, and verify current browser journeys. No clinical,
privacy, security, or regulatory approval is established by this audit.
