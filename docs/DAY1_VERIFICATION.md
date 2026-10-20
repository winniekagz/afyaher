# Day 1 verification — 20 October 2026

## Result

The Dockerized Next.js frontend and FastAPI backend are running and healthy on host loopback only:

- UI: http://127.0.0.1:3000
- API: http://127.0.0.1:8000/api/v1/health
- API response: `{"status":"ok","service":"afyaher-api"}`

The page shows loading, connected, and safe error/retry states. Requests time out after five seconds. The user-provided palette is applied: mauve #C599B6, rose #E6B2BA, peach #FAD0C4, cream #FFF7F3. Dark plum provides readable text and controls. Main text, muted text, badge text, and button text have calculated contrast ratios of 13.36:1, 6.45:1, 5.79:1, and 8.18:1 respectively. These checks do not constitute a full accessibility audit.

No medical advice, medical inputs, RAG, model generation, accounts, database infrastructure, or paid AI calls were added. The intended audience is adults 18+, and development is private and synthetic. The audience notice is not age verification.

## Files changed

- Root guidance: preserved legitimate AGENTS.md instructions, removed the unrelated copied browser-data suffix, and appended the approved Day 1 agreement. Updated CLAUDE.md and .github/copilot-instructions.md so both enforce the same standards and distinguish Day 1 connectivity from the subsequent PCOS slice.
- Root setup: README.md, .gitignore, compose.yaml, docs/DAY1_PLAN.md, and this report.
- Backend: pyproject.toml, uv.lock, .python-version, .env.example, Dockerfile, .dockerignore; package initializers; app/main.py, app/core/config.py, app/api/v1/health.py, app/schemas/health.py; tests/test_health.py.
- Frontend: package.json/package-lock.json, next.config.ts, postcss.config.mjs, app/page.tsx, app/layout.tsx, app/globals.css, lib/api.ts; README.md, .gitignore, .env.example, .prettierignore, Dockerfile, .dockerignore; Vitest and Playwright configurations, unit tests, and e2e/health.spec.ts. Existing starter assets were retained.

## Commands and outcomes

Commands ran in their respective frontend/backend directories unless noted. Temporary cache variables were used where the managed environment made home-directory caches read-only.

| Command | Outcome |
| --- | --- |
| `uv sync --cache-dir /tmp/afyaher-uv-cache` | Installed and locked backend dependencies in an isolated Python 3.13 environment |
| `uv run --cache-dir /tmp/afyaher-uv-cache pytest` | 8 passed; one upstream Starlette/HTTPX deprecation warning |
| `uv run --cache-dir /tmp/afyaher-uv-cache ruff check .` | Passed |
| `uv run --cache-dir /tmp/afyaher-uv-cache ruff format --check .` | Passed after formatting one test file |
| `npm install --cache /tmp/afyaher-npm-cache --no-audit --no-fund --fetch-timeout=30000 --fetch-retries=1 --maxsockets=5` | Clean installation succeeded and updated package-lock.json |
| `npm ci --cache /tmp/afyaher-npm-cache --no-audit --no-fund --fetch-timeout=30000 --fetch-retries=1` | Restored locked host dependencies for final checks |
| `npm run test` | 12 passed: 9 API-boundary tests and 3 UI tests |
| `npm run lint` | Passed with no final lint warnings |
| `npm run typecheck` | Passed |
| `npm run format:check` | Passed |
| `npm run build` using Webpack | Passed outside the sandbox |
| `PLAYWRIGHT_BROWSERS_PATH=/tmp/afyaher-playwright npx playwright install chromium` | Installed Chromium outside the sandbox |
| `npm run test:e2e` | Initially blocked by an existing AfyaHer Next.js process on port 3000; no browser tests ran in that attempt |
| `docker compose config --quiet` | Passed |
| `docker compose build` | Both images built; frontend production build and TypeScript check passed |
| `docker compose up --build -d --wait` | Rebuilt with the palette; both services healthy |
| `docker compose ps` | Both services healthy; only 127.0.0.1:3000 and 127.0.0.1:8000 published |
| `docker compose exec -T backend .venv/bin/python -c ...` | Live HTTP check returned the exact health JSON |
| `PLAYWRIGHT_BROWSERS_PATH=/tmp/afyaher-playwright npm run test:e2e:docker` | 3 passed against actual running containers |
| `git -C frontend diff --check` | Passed |

Additional inspection used rg, directory listings, tool version checks, git status/log, findmnt, and socket/process inspection. No repository initialization, history rewrite, commits, or public deployment were performed. The confirmed local AfyaHer development server was stopped to free port 3000 before Compose started.

The final browser suite checks real API connectivity, mobile overflow, loading/error/retry recovery, and an actual stalled request reaching the retry state. A screenshot of the running palette was saved under frontend/test-results/health-mobile-page-connects-to-the-real-FastAPI-backend-mobile-chromium/mobile.png and visually inspected. Test artifacts are ignored.

## Failures encountered and resolutions

- Restricted network/DNS blocked initial npm, uv, and Chromium downloads. Approved unrestricted retries succeeded.
- The first npm installers stalled while updating the existing dependency tree. Stopped the task's installers and preserved the old dependency folder at /tmp/afyaher-node_modules-day1-backup; a clean install succeeded. A later check found host development tools absent; npm ci restored them, and the final unit/lint/type/format checks passed.
- FastAPI TestClient stalled in the restricted environment. Its unrestricted run passed all eight tests.
- Turbopack failed to bind its CSS worker port, including an unrestricted retry. Switched to Next.js's supported Webpack option. A restricted Webpack build also failed parsing subprocess TypeScript output; unrestricted and Docker builds passed.
- Initial lint reported an anonymous PostCSS export warning; a named configuration export resolved it.
- The first browser attempt found port 3000 occupied. Confirmed that the process belonged to this AfyaHer frontend, stopped it, then ran the same browser scenarios successfully against Docker using a config that does not launch duplicate servers.
- Dependency installs reported upstream deprecations for ESLint 9 and whatwg-encoding; backend tests reported the Starlette/HTTPX warning. These remain dependency-maintenance items, not failing final checks. No dependency audit or clinical validation is claimed.

## Remaining gaps and Day 2

1. Import/reconcile the existing MVP PRD, architecture, and system-design documents. They were absent, and no replacement approved PRD has been invented.
2. In a normal writable checkout, plan a root-monorepo migration preserving frontend's existing main history (initial commit 05ee822). Root .git is an empty read-only tmpfs, and root/backend changes are outside the nested frontend repository. Back up the full workspace before migration.
3. Define the PCOS education slice's acceptance criteria, evidence provenance/review statuses, and safety/abstention contracts. Start source-backed content work only within the next approved slice, using synthetic examples.
4. Configure/verify coding-tool accounts, Copilot availability, and Anthropic API billing privately. These account settings were not changed or tested. Runtime AI credentials are not needed for Day 1.
5. Clinical, privacy, security, and applicable regulatory reviews remain prerequisites for real-patient or public use.

Containers are deliberately left running. Use `docker compose logs --tail=50`, `docker compose up --build -d --wait` after changes, and `docker compose down` to stop.

## Follow-up: local port 3001 connection fix

A screenshot showed a second frontend running on 127.0.0.1:3001 displaying a connection error. The original backend CORS list allowed only port 3000. Added the exact 127.0.0.1 and localhost origins on port 3001 to backend defaults, the example environment, and Compose configuration. No wildcard origins were introduced. Updated regression tests: 12 backend tests passed; Ruff lint and formatting passed. Rebuilt and restarted the backend container, which is healthy. The Docker frontend remains on port 3000. Live response headers confirmed both port 3001 origins are allowed while port 3002 remains excluded. The existing upstream Starlette/HTTPX warning remains.
