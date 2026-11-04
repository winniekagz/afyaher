# Current educational API data flow

Updated 4 November 2026 after the strict-validation and truthful-UI milestone.
This describes implemented behavior, not an approved replacement system design.
See [verification](API_VALIDATION_VERIFICATION.md) for executed checks.

| User action | Execution | Display and provenance boundary |
| --- | --- | --- |
| Select a suggested question | `demoAssistant` reads a fixed local editorial example; no HTTP request | Marked Demo/unreviewed, with a reference for that fixed example. It is not a retrieved/claim-validated citation |
| Submit typed synthetic text | `apiAssistant` calls `POST /api/v1/education/ask` through `lib/api.ts` | Shows real backend status, text, limitation and exact disclaimer. Current backend always returns `service_unavailable` and no sources |
| Malformed response or HTTP/network/timeout failure | API boundary rejects; panel catches without displaying raw details | Generic error and retry; original user message appears once, no partial answer/citations |
| Navigate to another page and back | React provider retains topic-specific messages/drafts in memory | Refresh clears them; no localStorage/sessionStorage or chat backend introduced |

The request still contains only `topic` and `question`; local `exampleIndex` is
never sent. The existing 500-character textarea cap is unchanged. Backend validation
still independently requires three non-whitespace characters, supported topic and
at most 2,000 characters after trimming. Short typed requests receive a safe generic
error on the backend's 422; no symptom classifier is involved.

## Runtime response checks

`frontend/lib/api.ts` treats JSON as `unknown`, checks it with small type guards,
and constructs a fresh typed object. It does not cast an unchecked payload into
the response type. Checks include object shape, existing status enum, supported
and matching topic, string question matching backend-normalized submitted text,
string answer, sources array and every required source field, HTTP(S) URL, required
string-or-null limitations, and the exact backend disclaimer literal.

Question normalization matches Python `str.strip()` whitespace, including U+0085
and control separators, and preserves BOMs that Python does not remove. An
unavailable response containing sources is rejected as inconsistent with the
current stub; it is not silently turned into a partial answer.

The adapter preserves complete validated source metadata and the existing source
ID list. If relevant API references are ever returned, the panel uses their own
validated title/publisher/URL instead of borrowing a static frontend entry. Links
open with `noopener noreferrer`; the label says claim support is not assessed.
The actual unavailable endpoint produces no references and the UI renders none.

## Current limitations

No backend route/schema or stub behavior changed. No model/provider, retrieval,
medical generation, clinical classifier, database, browser persistence, analytics
or question logging was added. The prior CI task's explicitly approved Vitest
upgrade is recorded separately in [CI verification](CI_VERIFICATION.md).

Client response validation is not source authorization, passage traceability or
medical claim verification. Those backend components remain separate and are not
connected to the question route. Reserved response statuses do not imply that the
stub provides those capabilities. Fixed medical examples/notices remain unreviewed.

Typed text really crosses the browser/API boundary. Backend defaults still echo
questions and can include input in 422 errors; education responses lack explicit
no-store protection. No full privacy, security, clinical or regulatory readiness
is claimed. Keep development private and synthetic.

The next smallest milestone is a separately approved backend privacy-boundary
task: agree input echo/error contracts, sanitize errors, add no-store and verify
that logs/telemetry never capture raw questions. It should precede real-user input;
generation remains unavailable throughout.
