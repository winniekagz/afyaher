# Strict API validation and truthful assistant UI verification

Date: 4 November 2026. Implemented the user's focused milestone after the audit.

## Specifications and scope

Reconciled repository instructions, supplied Word PRD/architecture drafts, audit,
gap analysis, roadmap, next-task proposal and actual FastAPI schemas/stub. The
system-design document remains missing; its contents were not invented.

Kept the public API and backend unavailable stub unchanged, including HTTP-200
application status semantics, three topics and existing validation rules. Kept
the frontend 500-character cap, design system, memory-only state and demo examples.
No medical generation, classifier, retrieval/DB integration, analytics or new
runtime dependency was added. The CI task's separate approved Vitest upgrade is
documented in `CI_VERIFICATION.md`.

## Files and behavior

| File | Before → after |
| --- | --- |
| `frontend/lib/api.ts` | Partial presence checks plus cast → guards for all consumed fields and fresh validated response construction; exact status/topic/question/disclaimer matching and source metadata/HTTP(S) checks |
| `frontend/lib/services/assistant.ts` | API source metadata reduced to IDs → preserve complete validated references alongside existing IDs and all status/limitation/disclaimer values |
| `frontend/components/assistant/assistant-panel.tsx` | Unavailable outcome replaced by demo limitation → real unavailable status/answer/limitation/disclaimer displayed, no citations; local API transfer explained before submission; suggestions remain fixed Demo examples |
| `frontend/tests/api.test.ts` | Add malformed/missing/type/status/topic/question/source/URL/disclaimer and Unicode-normalization cases, valid sources, existing statuses and invalid JSON |
| `frontend/tests/assistant-service.test.ts` | Assert complete metadata and unavailable fields survive adapter mapping |
| `frontend/tests/assistant-panel.test.tsx` | Assert truthful notice, exactly one POST with two fields, no API for suggestions, visible unavailable/limitation/disclaimer, no unsupported references; ten error/retry cases preserve one user message and hide raw error data; valid API metadata uses its own link |
| `frontend/e2e/learning.spec.ts` | Verify actual stub POST/result, zero API calls for suggestions, refresh clearing and malformed-response retry against local API, while retaining existing journeys |
| Root/frontend READMEs, `docs/API_INTEGRATION.md`, this report | Current data flow and limits; historical audit/verification reports left intact |

The accompanying CI task also changes test tooling/formatting, workflow/config
files and standards. Those are separate from the three application-source files
above. Production browser configuration now uses the built standalone server,
copies its existing public/static assets and binds to loopback; it does not alter
application behavior or weaken assertions.

## Runtime strategy

Treat JSON as unknown. Check non-array object, existing enum, supported matching
topic, string question matching Python-compatible whitespace normalization, string
answer, source array and every nonblank id/title/publisher/HTTP(S) URL, string-or-null
limitations and exact backend disclaimer. Reject sources on the current unavailable
stub rather than showing a partial result. Build a fresh typed response without an
unchecked type assertion.

Python `str.strip()` includes U+0085/control separators and excludes BOM; explicit
tests protect that difference from JavaScript `trim()`. API references retain
their own metadata, and the UI labels claim support as unassessed. Editorial demo
references remain separate and unreviewed. None of these checks proves medical
support, passage authenticity or clinical sufficiency.

## Test-first evidence and executed commands

Before application changes, the targeted regression run executed 79 tests:
**34 failed, 45 passed**. It reproduced weak validation, lost source metadata,
hidden unavailable fields and missing pre-submission API disclosure. Application
changes then made the suite pass. One additional positive metadata test brought
the final full frontend suite to 89 tests (52 more than the prior 37-test baseline).

Commands below ran from `frontend/` unless otherwise noted.

| Command | Actual final result |
| --- | --- |
| `npm run test` | 89 passed across seven files, Vitest 4.1.12 |
| `npm run lint` | Passed |
| `npm run typecheck` | Passed: route types and TypeScript |
| `npm run build` | Passed: compilation, TypeScript and all static/dynamic routes; unrestricted local build approved for this new task after known sandbox `--showConfig` parsing failures |
| `npx --no-install prettier --check lib/api.ts lib/services/assistant.ts components/assistant/assistant-panel.tsx tests/api.test.ts tests/assistant-service.test.ts tests/assistant-panel.test.tsx e2e/learning.spec.ts` | Passed (same installed Prettier requested by the milestone; no dependency downloaded) |
| `cp -R public .next/standalone/` and `cp -R .next/static .next/standalone/.next/` | Prepared standalone production assets for local browser tests |
| `CI=true PLAYWRIGHT_BROWSERS_PATH=/tmp/afyaher-playwright UV_CACHE_DIR=/tmp/afyaher-uv-cache npm run test:e2e` | Final full run: 18 passed in 16.2 seconds across mobile/desktop Chromium, real local FastAPI stub and standalone production frontend |
| `.venv/bin/pytest -q` from `backend/` | 319 passed, one existing Starlette/HTTPX deprecation warning, 1.66 seconds |

The matching browser was available after the approved CI-environment installation;
the audit's missing-browser blocker is resolved locally, not retroactively marked
as passing in old reports. Temporary test servers completed their runs; no public
service was deployed. Only synthetic typed text was submitted.

An initial production run passed 16 tests and failed the two new malformed-response
cases because `getByRole('alert')` also matched Next.js's route announcer. Scoped
the selector to the conversation log and reran all 18 successfully. The initial
production test command also warned that `next start` is inappropriate for
standalone output; the final verified command uses the standalone entry point.

The earlier development-server CI run's two reload-related conversation failures
are recorded separately; production verification does not claim to repair dev
Fast Refresh. No retry policy or assertion was relaxed to conceal failures.

## Remaining limits and next step

The assistant is still unavailable. No clinically reviewed safety/scope, medical
claim-support, answer generation or output pipeline is connected. The API still
echoes normalized questions and framework 422 errors can include raw input;
education responses lack explicit no-store protection. Client-safe errors do not
establish complete backend privacy. The 500 UI / 2,000 backend cap difference is
unchanged by explicit instruction.

No final current-source Docker rebuild is claimed: that execution request was
declined during the CI task. The host production build and current production
browser suite did pass. GitHub-hosted workflows/branch settings still need remote
activation, and 16 moderate npm dev-tool advisories remain for triage.

Recommended next milestone: separately approve and test backend error sanitization,
question echo minimization and response cache policy, keeping the route unavailable.
Source revisions, qualified content/safety review and claim-support contracts
remain dependencies for any later medical answering work.
