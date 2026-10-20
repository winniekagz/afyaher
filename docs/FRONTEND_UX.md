# AfyaHer frontend experience

Implemented from the user's approved six-screen UX brief and plan. The existing Day 1 constraints remain the foundation; the subsequent approval explicitly authorizes static educational content, source transparency, a labeled local assistant demo, and appointment-question editing. No database, authentication, live AI, RAG, or paid provider calls were added.

## Routes and components

| Route | Experience |
| --- | --- |
| `/` | Original AfyaHer welcome, topic search, three guided pathways, condition cards, trust/privacy explanation |
| `/conditions` | Searchable library for PCOS, ovarian cysts, and ovarian torsion; clear empty state |
| `/conditions/[slug]` | Article, native accessible disclosure sections, references, contextual assistant and appointment links |
| `/ask?topic=pcos` | Topic-aware, explicitly labeled demo; fixed examples, source links, loading, error/retry, limitation responses |
| `/sources/[sourceId]?topic=pcos` | Publisher, original URL, dates, relevant source context, reuse limitations, and unreviewed AfyaHer status |
| `/appointment?topic=pcos` | Editable/removable questions, custom additions, 15-question cap, clipboard success/failure feedback |
| `/dev/status` | Preserved FastAPI connectivity check with loading, success, error, and timeout handling |

Shared components live under `frontend/components/`: layout/provider, navigation, UI primitives, condition cards/search, article, assistant, and appointment editor. Typed content metadata lives in `frontend/lib/content/conditions.ts`; `frontend/lib/services/assistant.ts` isolates the local demo contract from a future FastAPI adapter. Existing `lib/api.ts` remains the real health API boundary.

## Design

- Existing cream, mauve, rose, peach, and plum tokens retained, with clear border/text roles.
- Georgia headings and system sans-serif body text; no external font downloads.
- Mobile bottom navigation and a distinct desktop header. Saved is omitted because bookmarks are unsupported.
- Responsive cards, restrained original line decoration, and Lucide icons; no Flo branding or assets copied.
- Visible focus, skip link, form labels, semantic landmarks, native disclosure sections, reduced-motion handling, and generous control sizes. This is WCAG-conscious implementation, not a claimed full accessibility certification.

## Demo, safety, and privacy boundaries

There is no assistant backend endpoint yet. Suggested examples return fixed editorial paragraphs and their real reference. Arbitrary typed input receives an explicit limitation without a fabricated citation. The demo makes no medical assessment, retrieval, safety decision, or model call. Request/answer types include outcome statuses, and the UI preserves them. A future live adapter must validate runtime responses and render backend safety outcomes faithfully.

The demo rejects unknown source references rather than displaying unsupported answers. This checks reference integrity; it does not establish medical accuracy or constitute RAG citation validation. The prototype has no clinical reviewer. Static urgent-care messaging appears prominently on the assistant, torsion article, and torsion appointment context. It is always displayed in the assistant, not activated by a purportedly reliable frontend symptom filter. It cannot rule out an emergency.

User messages and appointment drafts remain in a React provider in memory. They survive client navigation and browser back within the session; refresh clears them. There is no localStorage, sessionStorage, chat backend, question analytics, or raw-question logging. Topic/source IDs alone are used for route context. Inputs have length limits. Only synthetic/general inputs should be used during private testing.

## Content provenance

Checked against original publishers during development on 20 October 2026:

- [WHO: Polycystic ovary syndrome](https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome), publication date 22 January 2026. Overview and diagnosis sections support the concise PCOS examples.
- [NHS: Ovarian cyst overview](https://www.nhs.uk/conditions/ovarian-cyst/), page last reviewed 21 June 2023. Its listed review due date was 21 June 2026; a newer review was not confirmed and this limitation is exposed in source details.
- [BMJ: Ovarian torsion patient information](https://bestpractice.bmj.com/patient-leaflets/en-us/download/3000299/Ovariantorsion.pdf), last published 18 January 2023. Pages 1–2 support the brief definition and urgency context. The UI identifies it as an older leaflet, not a current clinical guideline.

AfyaHer summaries are brief original paraphrases, not copied articles. Sources are linked rather than ingested or stored. Broader reuse permissions are unverified. Publisher credentials or dates do not imply that AfyaHer content has undergone clinical review or that publishers endorse the app.

## Verification

- `npm run test`: 26 passed across seven files. Covers preserved API states, search/empty recovery, fixed demo references, arbitrary-question abstention, oversized input, assistant loading/error/retry, unknown-source rejection, appointment editing/removal/addition, clipboard failure, empty lists, and preservation of topic context in global navigation.
- `npm run typecheck`: passed.
- `npm run lint`: passed.
- Docker's `npm run build`: passed; all static and dynamic routes built, including standalone runtime output.
- Final browser suite: **16 passed in one complete run** against the final production frontend/backend stack on ports 3002/8001. Covers mobile and desktop Chromium, global navigation with non-PCOS topics, real health API connectivity, full PCOS/source/appointment flow, browser back, clipboard copy, refresh clearing, demo limitations, torsion notices, tablet overflow checks, and keyboard skip navigation.
- Earlier verification found two test timeouts caused by an exact-text accordion selector including a decorative plus sign. The selector was corrected and those targeted checks passed before the final complete run. An initial formatting check also identified the test configuration file; it was formatted and the final check passed.
- All six screens passed additional horizontal-overflow checks at 320px, 390px, and 1440px; tablet checks at 820px passed in Playwright. Home, article, assistant, source details, and appointment screenshots were visually inspected. Final polish gives input boundaries a darker mauve token and keeps icon controls at least 44px.

Development-only test artifacts are ignored by Git. No new backend behavior was introduced; the existing health endpoint is exercised by browser tests.

## Running in this workspace

The host Docker daemon denied permission to stop both the old frontend on port 3000 and the first preview on port 3001. Neither was forcibly removed and no host security settings were changed. The final frontend/backend pair runs in an isolated Compose project with the same architecture:

```bash
docker compose -p afyaher-ux -f compose.yaml -f compose.preview.yaml up --build -d --wait
```

Open **http://127.0.0.1:3002**. The preview API is at **http://127.0.0.1:8001/api/v1/health**. The override sets those host ports, the frontend's API build argument, and the matching explicit backend CORS origins. The final frontend and backend reported healthy after startup. Old versions on 3000/3001 are not the final build. All published ports remain loopback-only. Standard fresh-environment deployment still uses `docker compose up --build -d --wait` and ports 3000/8000.

From `frontend/`, run `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3002 npm run test:e2e:docker` against the final stack. If using the managed workspace's browser cache, include `PLAYWRIGHT_BROWSERS_PATH=/tmp/afyaher-playwright`.

## Remaining integration and release work

The PRD, architecture, and system-design source documents are still absent. Import and reconcile them before further scope expansion. Existing root Git metadata remains an environment restriction; nested frontend history and existing staging were preserved.

Implement the real validated question endpoint, backend safety screening, evidence retrieval, source provenance/review workflow, citation/claim checks, and safe failure behavior before enabling live AI. Clinical review, privacy/security review, and applicable regulatory assessment remain necessary before real-patient or public use. Accounts, bookmarks, durable drafts, and personal medical inputs remain outside this implementation.
