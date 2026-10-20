# AfyaHer

Private, mobile-first reproductive-health education prototype for adults (18+), initially focused on PCOS, ovarian cysts, and ovarian torsion. Development uses synthetic scenarios only. There is no clinical reviewer yet; this is not a diagnostic or treatment service and must not be used with real patients or released publicly before the appropriate reviews.

## Day 1 scope and status

Next.js presents a local connection check; FastAPI owns a versioned, Pydantic-validated health endpoint. The page has loading, connected, error, and retry states. There are no medical-question inputs, AI calls, databases, accounts, uploads, or stored chats.

The broader approved architecture is a modular FastAPI monolith with a Next.js UI. PostgreSQL/pgvector, SQLAlchemy/Alembic, hosted model/embedding APIs, RAG, safety screening, and citation validation belong to later milestones. Do not move domain logic into Next.js.

`docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/SYSTEM_DESIGN.md` were absent during setup. This implementation follows the user's approved Day 1 requirements and existing project instructions; it does not replace or claim to implement an unseen PRD. See [Day 1 decisions](docs/DAY1_PLAN.md) and [verification report](docs/DAY1_VERIFICATION.md).

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
docker compose up --build -d --wait
docker compose ps
docker compose logs --tail=50
```

Open http://127.0.0.1:3000. The API is at http://127.0.0.1:8000/api/v1/health. Both host ports bind only to loopback. Containers run as non-root users and have health checks. Stop them with `docker compose down` before running the local Playwright servers.

The browser calls the API on the host's loopback address, not the internal Docker service name. The public API URL is a frontend build argument; rebuild the frontend if it changes. The containers contain no secrets, personal data, database, or AI service. Initial builds download base images and locked dependencies. Use `docker compose up --build -d --wait` after source changes; source files are not bind-mounted.

With the containers running, use `npm run test:e2e:docker` from `frontend/` to run the browser checks without starting duplicate servers.

The UI palette uses mauve `#C599B6`, rose `#E6B2BA`, peach `#FAD0C4`, and cream `#FFF7F3`, with darker plum text and buttons for readable contrast.

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

`GET /api/v1/health` returns HTTP 200, JSON, and `Cache-Control: no-store`:

```json
{"status":"ok","service":"afyaher-api"}
```

This is a liveness check only. It says nothing about medical safety, databases, model readiness, or clinical approval. The frontend validates both response values and bounds the request to five seconds. Invalid JSON, HTTP errors, timeouts, and network failures all show a safe retry state.

## Checks

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

## Git limitation

The environment exposes an empty read-only tmpfs at the root `.git/`, so the root is not a usable repository. `frontend/.git/` contains an existing `main` history, including `05ee822` (Create Next App initial commit). It has been preserved. Do not initialize over either location or delete/move metadata blindly. A history-preserving migration to a root monorepo must be performed in a normal writable checkout. Until then, frontend Git status does not include backend or root documentation changes; back up the entire workspace.
