# CI, development standards and build verification

Date: 4 November 2026. This records the CI/standards task and its explicitly
approved Vitest upgrade. The subsequent API/UI implementation is recorded in
[API_VALIDATION_VERIFICATION.md](API_VALIDATION_VERIFICATION.md).

## Changes

- Root backend/frontend GitHub Actions workflows, plus standalone frontend CI.
- Exact recorded frontend checkout; repaired `.gitmodules` using the existing
  remote without rewriting or flattening histories.
- Official actions pinned to verified full commit hashes; read-only permissions,
  finite job timeouts, no persisted tokens, no image publishing or deployment.
- Weekly Dependabot configurations in both repositories; CODEOWNERS and a root
  PR template. Server-side rulesets, scanning and secrets require owner setup.
- Root/standalone frontend contributing standards, root security policy and
  `.editorconfig`; documented private-source checkout and review requirements.
- Existing backend/frontend formatting failures corrected without behavior changes.
- User-approved Vitest 3.x → 4.1.12 upgrade, lockfile and config migration to
  `.mts`/Oxc; no existing production package version changed.
- Production standalone server for root browser CI, with public/static assets
  prepared before tests and loopback hostname/port explicitly configured.

## Actual checks

| Command / check | Actual outcome |
| --- | --- |
| Official `git ls-remote` for actions/checkout v6, actions/setup-node v6, astral-sh/setup-uv v7 | Resolved official commit references after sandbox DNS failure and an approved retry; pinned concrete commits in all workflows |
| Python/PyYAML parse of five YAML files, with workflow trigger/permission/timeout/action-pin assertions | Passed; this is a syntax/basic-policy check, not a hosted GitHub Actions run or full actionlint validation |
| `docker compose config --quiet` | Passed |
| `.venv/bin/ruff check .` and `.venv/bin/ruff format --check .` from backend | Passed; 31 Python files formatted |
| `.venv/bin/pytest -q` from backend | 319 passed, one existing Starlette/HTTPX warning |
| `npm run format:check`, `npm run lint`, `npm run test`, `npm run typecheck` before tool upgrade | Passed; 37 unit tests |
| `uv audit --locked --cache-dir /tmp/afyaher-uv-cache` from backend | Sandbox DNS blocked first attempt; approved unrestricted retry passed: no known vulnerabilities/adverse statuses in 26 packages. Native uv audit emits an experimental-feature warning |
| `npm --cache /tmp/afyaher-npm-cache audit --audit-level=high` before upgrade | Failed as intended: 19 findings, 17 moderate and 2 critical in the test-tool dependency chain; not ignored |
| Approved `npm install --save-dev 'vitest@^4.1.12' ...` | In-place installer stalled; stopped only that task's process. Preserved old node_modules under `/tmp/afyaher-node-modules-before-vitest4-20261104`; generated lockfile with package-lock-only and installed cleanly with `npm ci` |
| `npm ci --cache /tmp/afyaher-npm-cache --no-audit --no-fund --fetch-timeout=30000 --fetch-retries=1` | Installed 464 packages successfully; existing whatwg-encoding/ESLint deprecation warnings remain |
| Tests/type checking immediately after upgrade | Unit tests passed; type check failed on the old esbuild JSX config. Migrated it to `.mts` and `oxc.jsx.runtime`, then unit/lint/type/format checks passed |
| `npm --cache /tmp/afyaher-npm-cache audit --audit-level=high --fetch-timeout=30000 --fetch-retries=0` after upgrade | Exit 0 at configured threshold: no high/critical findings; 16 moderate findings remain in ESLint/minimatch chain. No force-fix, downgrade or audit exception was applied |
| `docker compose build` before dependency/UI changes | Both backend and frontend images built, including production frontend compilation/type checking. Sandbox build-cache write was blocked; approved unrestricted retry passed |
| Docker rebuild during Vitest migration | Backend built; frontend failed type checking because its build context captured the old esbuild config before migration. Corrected source config passes host type checking/build |
| Final Docker rebuild permission request | Rejected at the execution-permission prompt. No repeat request or deployment was made; final updated frontend image remains unverified. Earlier image success is not claimed for the current UI |
| `PLAYWRIGHT_BROWSERS_PATH=/tmp/afyaher-playwright npx --no-install playwright install chromium` | Installed matching Chromium/headless-shell 1248 and FFmpeg 1013 in /tmp, with permission; no application dependency added |
| Development-server Playwright run | 14 passed, 2 PCOS-journey failures; logs showed a dev reload resetting in-memory conversation. Did not disable assertions or add retries to hide it |
| Follow-up production standalone browser run after the API/UI task | 18 passed; current-state details and exact command in API verification. Development-mode reload behavior is not claimed fixed |
| Final host `npm run build` for the API/UI task | Passed with current lockfile/config and application changes; this is not a Docker rebuild |

Audit commands query public advisory services with dependency metadata, not user
questions. Slow/default npm audit calls and sandbox network failures were retried
with network permission and bounded fetch options. No lockfiles were changed by
audit itself. No raw health questions, secrets or production approval records were
introduced.

## Activation and remaining work

These workflows have not run on GitHub. Push the frontend revision before the root
Git link, configure a read-only frontend checkout token if the separate repository
is private, then enable branch required checks/review and supported scanning in
GitHub settings. Those account settings were not changed by this task.

Triage the remaining moderate dev-tool advisories and the deprecated ESLint line
in a separately approved compatibility change. Verify a final current-source
Docker build when execution is authorized. Do not interpret successful technical
checks as a clinical, security or regulatory sign-off. Medical generation and
public use remain gated by the audited release requirements.
