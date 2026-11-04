# Recommended next task: a strict, truthful unavailable API journey

Status: implementation proposal awaiting audit review and scope approval.
Date: 4 November 2026. Do not implement as part of Step 7.

## Goal

A synthetic typed question traverses the existing Next.js→FastAPI boundary and
shows the actual `service_unavailable` outcome and safe limitation. Malformed or
mismatched responses fail explicitly. Suggested questions remain clearly separate
fixed demo examples. No medical answer generation is introduced.

Why this first: the transport adapter already exists, but the panel hides the
unavailable result and the response parser accepts invalid field types. Repairing
this narrow path provides testable progress without requiring clinical sufficiency
criteria, a database, embeddings, or a model. See gap findings G09, G10 and G15.

## Existing contracts to preserve

- `POST /api/v1/education/ask`, HTTP 200 for valid input, application outcome
  `service_unavailable`, empty sources, fixed answer/limitation/disclaimer.
- The public request remains `{topic, question}`. `exampleIndex` stays local.
- Backend validates topics, ≥3 non-whitespace characters, and ≤2,000 after trim.
  The separate 500-character frontend cap is a product decision tracked in G11;
  do not silently alter public schema or backend checks in this task.
- Keep health API behavior, brand, topic context, memory-only conversation state,
  generic safe error rendering, and local fixed examples.

## Proposed files

| File | Focused change |
| --- | --- |
| `frontend/lib/api.ts` | Validate every education-response field and nested source against the existing backend contract; reject unknown statuses, unsupported/mismatched topic, malformed source metadata and HTTP(S) URL, wrong field types, missing/incorrect disclaimer, and inconsistent returned question. Normalize request/echo comparison using existing trim behavior |
| `frontend/lib/services/assistant.ts` | Preserve the validated unavailable outcome, limitation and disclaimer in the existing API answer type; avoid unnecessary contract redesign |
| `frontend/components/assistant/assistant-panel.tsx` | Remove unavailable→demo substitution; render the actual limitation/disclaimer; explain that typed synthetic questions are sent to the local API while suggestions are local fixed examples. Keep transport failure distinct from unavailable |
| `frontend/tests/api.test.ts` | Malformed and mismatched runtime payload cases; valid unavailable payload; timeout, network and 422 cases |
| `frontend/tests/assistant-service.test.ts` | Preserve status/metadata unchanged and keep demo examples local |
| `frontend/tests/assistant-panel.test.tsx` | API unavailable display, loading/error/retry, no duplicate user message, no unsupported citations, clear mode/privacy wording |
| `frontend/e2e/learning.spec.ts` | Assert real synthetic POST body/response and unavailable outcome, separately from local fixed-example flow; preserve no browser-storage check |
| Documentation | Record actual verification and update current API/data-flow description; do not rewrite historical passing reports as present evidence |

Keep schema validation readable with existing TypeScript checks; no new validation
dependency is proposed. The exact disclaimer is already a backend literal.
Unknown extra response fields can follow the agreed compatibility policy; validate
all fields actually consumed rather than assuming a cast provides runtime safety.

## Acceptance criteria

1. A valid synthetic question produces one POST containing only topic/question.
   An available local stub returns `service_unavailable`, which remains visible;
   the panel never converts it into `answered` or a demo limitation.
2. Suggested examples still make no API/provider call and are explicitly marked
   fixed, unreviewed examples. Their citations remain editorial references.
3. The panel makes API transfer of typed text clear before submission. Keep the
   instruction to use synthetic text and avoid personal/medical details; do not
   imply that memory-only UI state means no server transfer occurs.
4. Valid unavailable limitations and disclaimer are displayed; no sources appear
   on this stub outcome. Preserve urgent-notice wording rather than inventing new
   clinical messages in this engineering task.
5. Missing fields, invalid nested sources/URLs, wrong answer/question/disclaimer
   types, unsupported/mismatched topic, and malformed status fail into a safe
   error state. A response cannot borrow the wrong topic/question's identity.
6. HTTP 422, timeout, malformed JSON and network failure give recoverable error
   feedback; retry does not duplicate the user message. Server stack/error text
   is not displayed.
7. Messages/drafts remain in React memory only and clear on refresh. Tests and
   screenshots use synthetic non-identifying content. No question/passage logs,
   analytics or persistence are added.
8. Existing backend stub, source eligibility, provenance gate and frontend
   navigation/design remain unchanged. No result from Step 6 authorizes answers.

## Tests and verification

First add failing runtime payload and unavailable-panel tests, then make the
smallest fixes. Run from `frontend/`:

```bash
npm run test
npm run lint
npm run typecheck
npm run build
npx prettier --check lib/api.ts lib/services/assistant.ts components/assistant/assistant-panel.tsx tests/api.test.ts tests/assistant-service.test.ts tests/assistant-panel.test.tsx e2e/learning.spec.ts
UV_CACHE_DIR=/tmp/afyaher-uv-cache npm run test:e2e
```

Browser verification requires the matching Playwright Chromium revision 1248,
which is missing in the audit environment. Approve/install it through normal
environment setup, then run the configured suite; do not present launch failures
as product assertions. Avoid running type generation/build and dev server at the
same time against one `.next` directory. Backend regression command from
`backend/`: `.venv/bin/pytest -q`. Report current formatting baselines separately
and format touched files only as needed.

The above commands are the proposed implementation checks. Step 7's actual
outcomes are recorded in the current-state audit; none are newly claimed here.

## Safety boundaries and explicit exclusions

This task improves the existing private unavailable journey. It does not approve
real-user input or public use: G06–G08 and G23 remain release blockers. Backend
sanitized errors/no-store/rate/access controls are a separately approved next
privacy milestone; the UI should not promise they already exist.

No public API/schema changes, route changes, model/provider calls, safety
classifier, diagnosis, medication/treatment advice, evidence-sufficiency threshold,
medical answer generation, DB/Alembic, embeddings/vector search, real content
ingestion/approval changes, accounts/bookmarks, deployment, or frontend redesign.
No clinical/legal approval is implied by test results.

After this task, proceed to privacy-boundary hardening and reviewed specification,
source-revision, safety/scope and claim-support contracts according to the
[dependency-aware roadmap](AFYAHER_IMPLEMENTATION_ROADMAP.md).
