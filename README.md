# AfyaHer

Private, mobile-first reproductive-health education prototype for adults (18+), initially focused on PCOS, ovarian cysts, and ovarian torsion. Development uses synthetic scenarios only. There is no clinical reviewer yet; this is not a diagnostic or treatment service and must not be used with real patients or released publicly before the appropriate reviews.

## Current frontend prototype

Six connected screen types are implemented: Home (`/`), Condition Library (`/conditions`), Condition Detail (`/conditions/pcos` and the two other topic routes), Ask AfyaHer (`/ask?topic=pcos`), Source Details (`/sources/who-pcos?topic=pcos`), and Appointment Preparation (`/appointment?topic=pcos`). The original FastAPI health check remains at `/dev/status`.

The assistant is a **private prototype, not live AI**. Suggested questions return
local fixed, unreviewed examples with editorial references. Typed synthetic
questions are sent to the local FastAPI service; the UI displays its real
`service_unavailable` status, limitation and disclaimer without substituting a
demo response. Runtime checks reject malformed or topic/question-mismatched API
responses. Temporary conversation and appointment drafts survive client navigation
but clear on refresh; no browser persistence, analytics or provider calls were
added. Backend privacy controls remain incomplete: request/validation responses can
echo input, and education responses lack an explicit no-store policy. Use synthetic
questions only. See the [current API data flow](docs/API_INTEGRATION.md).

The design uses the existing palette, readable system fonts, responsive navigation, original decorative line work, and Lucide icons. Source pages expose publisher dates, context, permissions limitations, and the absence of AfyaHer clinical review. This frontend is an engineering prototype, not a clinically validated production product.

The broader approved architecture is a modular FastAPI monolith with a Next.js UI. PostgreSQL/pgvector, SQLAlchemy/Alembic, hosted model/embedding APIs, RAG, safety screening, and citation validation belong to later milestones. Do not move domain logic into Next.js.

The root `AfyaHer_PRD.docx` and `AfyaHer_Architecture.docx` are now available as
version-0.1 drafts. Canonical Markdown specifications and the system-design
document remain missing. The foundation follows approved incremental tasks; it
does not claim full implementation or approval of those drafts. See the
[current-state audit](docs/audits/AFYAHER_CURRENT_STATE_AUDIT.md) and subsequent
verification reports; older reports describe their own as-of state.

## Prerequisites

- Node.js satisfying the locked Next.js package's engine requirements (installed environment: 20.20.2).
- npm (installed: 10.8.2); use npm and commit `frontend/package-lock.json`.
- uv and Python 3.13 (selected by `backend/.python-version`); commit `backend/uv.lock`.
- A Playwright Chromium browser for end-to-end checks.

Development and build scripts explicitly use Next.js's supported Webpack option because Turbopack's CSS worker could not bind an internal port in this managed environment.

## Local setup

### Run both services with Docker

From the repository root:

```bash
cp -n backend/.env.example backend/.env
# Set a private local TYPESENSE_API_KEY in backend/.env before starting Compose.
docker compose --env-file backend/.env up --build -d --wait
docker compose ps
docker compose logs --tail=50
```

Open http://127.0.0.1:3000. The API is at http://127.0.0.1:8000/api/v1/health. Both host ports bind only to loopback. Containers run as non-root users and have health checks. Stop them with `docker compose down` before running the local Playwright servers.

The browser calls the API on the host's loopback address, not the internal Docker service name. The public API URL is a frontend build argument; rebuild the frontend if it changes. The local Typesense admin key is supplied to the Typesense and backend containers only; it is not included in the frontend. This phase has no database or AI service. Initial builds download base images and locked dependencies. Use `docker compose --env-file backend/.env up --build -d --wait` after source changes; source files are not bind-mounted.

With the containers running, use `npm run test:e2e:docker` from `frontend/` to run the browser checks without starting duplicate servers.

The UI palette uses mauve `#C599B6`, rose `#E6B2BA`, peach `#FAD0C4`, and cream `#FFF7F3`, with darker plum text and buttons for readable contrast.

### Current managed-workspace preview

The latest six-screen UI is at **http://127.0.0.1:3002** and its API is at **http://127.0.0.1:8001**. The host Docker daemon denies permission to stop older containers on ports 3000 and 3001. Those containers are preserved; they are not the latest build. An isolated frontend/backend pair uses the same approved architecture on alternate loopback ports:

```bash
docker compose -p afyaher-ux -f compose.yaml -f compose.preview.yaml up --build -d --wait
```

The override changes the host ports, frontend API build argument, and backend's explicit local CORS allowlist. It adds no database or external service. Resolving the host daemon's container-stop permission error is a separate host task; no system security settings were changed. When host permissions are corrected, use the same Compose arguments followed by `down` to stop this stack.

To check the running preview from `frontend/`:

```bash
PLAYWRIGHT_BASE_URL=http://127.0.0.1:3002 npm run test:e2e:docker
```

Use `PLAYWRIGHT_BROWSERS_PATH` too if Chromium was installed in a custom directory. See [frontend implementation and verification](docs/FRONTEND_UX.md).

### Run without Docker

From the repository root:

```bash
cd backend
uv sync --locked
cp .env.example .env
cd ../frontend
npm ci
cp .env.example .env.local
npx playwright install chromium
```

The example files contain local URLs only. No credentials or paid APIs are needed. If package-cache directories are read-only in a managed workspace, set `UV_CACHE_DIR=/tmp/afyaher-uv-cache`, `npm_config_cache=/tmp/afyaher-npm-cache`, and, for browser downloads, `PLAYWRIGHT_BROWSERS_PATH=/tmp/afyaher-playwright`. Use the same browser-path variable for installation and tests.

Run the backend in one terminal, from `backend/`:

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run the frontend in a second terminal, from `frontend/`:

```bash
npm run dev
```

Open http://127.0.0.1:3000. API docs are local at http://127.0.0.1:8000/docs. Both servers bind to loopback. The page's 18+ notice describes the intended audience; it is not age verification. Robots metadata discourages indexing but is not access control. Do not expose these servers through public hosting or tunnels.

If a separate frontend development server falls back to port 3001, the backend also allows the exact loopback origins `http://127.0.0.1:3001` and `http://localhost:3001`. Other origins remain blocked. If you have an older backend `.env`, update its `CORS_ORIGINS` list to match `.env.example` and restart the API. Docker's frontend remains on port 3000.

`NEXT_PUBLIC_API_BASE_URL` is a public browser setting, defaults to `http://127.0.0.1:8000`, and is embedded at build time. It must never contain credentials. The backend's `CORS_ORIGINS` is a JSON list; defaults allow only local frontend origins. CORS is a browser restriction, not authentication.

## API contract

Interactive Swagger documentation is at
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) when the backend is running.
ReDoc is at `/redoc`, and the live OpenAPI schema is at `/openapi.json`.
See the [API guide](docs/api/README.md) and the
[checked-in OpenAPI schema](docs/api/openapi.json) for synthetic examples and
current endpoint limitations. From `backend/`, regenerate the schema with
`uv run python -m scripts.export_openapi` after API documentation changes.

`GET /api/v1/health` returns HTTP 200, JSON, and `Cache-Control: no-store`:

```json
{"status":"ok","service":"afyaher-api"}
```

This is a liveness check only. It says nothing about medical safety, databases, model readiness, or clinical approval. The frontend validates both response values and bounds the request to five seconds. Invalid JSON, HTTP errors, timeouts, and network failures all show a safe retry state.

## Typesense retrieval phase

Typesense now provides topic-filtered text search over approved passage records.
The separate `POST /api/v1/knowledge/search` endpoint returns provenance-checked
candidates only; it does not call an LLM or claim that passages support an
answer. Empty results abstain, and retrieval failures do not fall back to the
development keyword retriever. The checked-in passage input is intentionally
empty because no medical passages have completed qualified review and
permission checks. See [Typesense local setup](docs/TYPESENSE_SETUP.md), the
[system design](docs/SYSTEM_DESIGN.md), and [AI safety boundary](docs/AI_SAFETY.md).

## Source registry

`backend/data/sources/pcos.json` stores source **metadata only**, with no article text. Each record is validated by `app/schemas/knowledge.py`. Clinical review status and legal ingestion permission are kept as separate fields. Unverified dates and licences are recorded as `null`. A source can be ingested automatically only when its permission is `permitted`, a licence plus authorisation evidence (`authorization_reference`, `authorization_date`) are recorded, **and** its clinical review is `approved` (`app/services/knowledge.py`). No source meets these conditions yet. `app/services/chunking.py` splits supplied text into `SourcePassage` records and refuses ineligible sources. `app/services/citations.py` maps cited passage IDs to registry metadata and rejects passages that were not retrieved or that come from an unknown or ineligible source. Both are tested only with synthetic text; nothing fetches content. To inspect a registry, run this from `backend/`:

```bash
uv run python -m scripts.inspect_sources [path/to/registry.json]
```

Every source also has a `content_scope` (`production` or `development_only`). A fictional, non-medical fixture lives separately in `backend/data/fixtures/synthetic/`, with `evidence_type: synthetic_fixture`. Synthetic fixtures must be `development_only`. They can be chunked (`can_chunk`), but they never pass `is_eligible_for_production_retrieval`, and `resolve_citations` rejects them. Chunking keeps every non-whitespace character in order; whitespace is normalised. To rebuild the fixture passages (`passages/*.json`), run this from `backend/`:

```bash
uv run python -m scripts.build_passages
```

Legacy source metadata without `content_scope` loads as `development_only`;
production evidence requires an explicit `production` scope plus all existing
permission and clinical-review checks. Unknown retrieval scopes are rejected.
Passage sets enforce their recorded size limit, sequential positions, and source
IDs. Citation resolution also rejects duplicate retrieved IDs and inconsistent
passage topic, ID, or position metadata. These checks establish traceability,
not medical claim support. See [Step 5 review and verification](docs/STEP5_VERIFICATION.md).

`app/services/retrieval.py` provides deterministic keyword retrieval over stored passages, as a stand-in for vector search. It has no embeddings or database. It defaults to the `production` scope, which excludes synthetic and development-only sources. An empty result means insufficient evidence. Queries are never logged or stored. To search the synthetic fixture (development scope only), run this from `backend/`:

```bash
uv run python -m scripts.search_passages "green lanterns"
```

The [PCOS knowledge-base starter](docs/knowledge-base/README.md) documents source
reuse restrictions and an optional hosted free-model experiment. The experiment
selects existing synthetic passage IDs only; the medical assistant remains
unavailable. FDA is a new unreviewed, development-only metadata candidate. No
medical source is approved for ingestion or production retrieval.

## Checks

[Development standards](CONTRIBUTING.md), [security standards](SECURITY.md), and
[GitHub Actions setup](docs/CI.md) define the required quality gates. Backend and
frontend workflows run on pull requests, main-branch pushes and manual dispatch;
they build images without publishing or deploying. Weekly Dependabot updates are
configured separately for the root and frontend repositories.

From `backend/`:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

From `frontend/`:

```bash
npm run test
npm run lint
npm run typecheck
npm run format:check
npm run build
npm run test:e2e
```

Playwright starts both actual servers on ports 3000/8000; stop manual servers before running it. It tests a mobile viewport, real backend connectivity, failure handling, and retry. Unit tests cover API payload validation and UI states. To format intentionally, use `uv run ruff format .` and `npm run format` in their respective directories. To run the built frontend locally, use `npm run start` after `npm run build`, alongside the backend.

## Coding tools and secrets

Claude Code is installed in the inspected environment. For Anthropic API billing, supply `ANTHROPIC_API_KEY` privately through the shell/secret environment used to launch Claude Code; never paste keys into chat, tracked files, or command examples. VS Code can use an Anthropic provider key through its model-management UI where BYOK is supported. Account permissions and billing are not configured or verified by this repository. Copilot's inline-completion features can require a separate Copilot service/plan.

Keep coding-tool credentials and budgets separate from future AfyaHer runtime credentials. Never put secrets into `NEXT_PUBLIC_*`, source files, screenshots, or logs. Commit only placeholder environment templates; real `.env` files are ignored. No paid calls were made for Day 1. Agent standards live in `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`.

Provider setup references: [Claude Code API-key billing](https://support.claude.com/en/articles/12304248-manage-api-key-environment-variables-in-claude-code), [VS Code language models](https://code.visualstudio.com/docs/agent-customization/language-models), and [Copilot feature limitations](https://code.visualstudio.com/docs/agents/agent-troubleshooting/faq). Recheck account-specific availability before enabling paid usage.

## Git layout

The root and `frontend/` retain separate histories. The root records the frontend
as a Git link, with its remote in `.gitmodules`; clone recursively to fetch both.
Commit and push frontend changes first, then update the root frontend pointer.
Root CI checks that exact revision. A private frontend repository needs the
read-only checkout setup described in [CI documentation](docs/CI.md). Do not
reinitialize or flatten either history. The managed sandbox may require permission
to write root Git metadata; both histories are now usable with that permission.
