# AfyaHer development standards

AfyaHer is a private adult educational engineering prototype. These standards
supplement `AGENTS.md`; they do not approve medical answers or public deployment.
Read the root PRD/architecture Word drafts, current audit and relevant decisions
before changing behavior. The system-design document remains unavailable; request
it rather than inventing its contents.

## Working agreement

- Inspect Git status and preserve other contributors' work. Make one focused,
  reviewable change per branch/PR and explain its purpose and limitations.
- Obtain approval for public schema, architecture, dependency, migration,
  provider/cost or deployment changes. Keep approved changes incremental.
- Keep UI/presentation in Next.js and domain/safety/evidence logic in FastAPI.
  Prefer readable functions and a modular monolith to new frameworks/services.
- Use npm with `package-lock.json`, uv with `uv.lock`, Python 3.13, and Node 22
  (the CI/container version). Install from lockfiles; never edit locks manually.
- Add behavior and failure-mode tests. Use synthetic, non-identifying scenarios.
  A test passing is not evidence of clinical safety or regulatory approval.
- Keep secrets, `.env`, caches, raw questions and sensitive artifacts out of Git.
  Document only placeholders in `.env.example`.

## Code conventions

Python: type hints, Pydantic boundary validation, thin routes, explicit services
and data access boundaries. Use Ruff lint/format and pytest. No backend type checker
is currently configured; do not claim one passes or add one without approval.

TypeScript: strict types, runtime validation at HTTP boundaries, accessible shared
components, labeled controls and explicit loading/error/empty states. Use ESLint,
Prettier, TypeScript, Vitest and Playwright. Preserve the existing AfyaHer palette
and design foundation. Do not store conversations in browser storage.

APIs: preserve `/api/v1/` contracts and document actual behavior. Update route
documentation and regenerate `docs/api/openapi.json` with
`uv run python -m scripts.export_openapi` after approved API changes. Distinguish
application statuses from HTTP status codes. Never expose stack traces or raw
health input through logs, analytics or error reporting.

Evidence: separate development fixtures, source permissions, clinical review and
production eligibility. Do not mark a source approved without qualified review.
Valid citation IDs and lexical scores do not establish claim support. Every
provenance-gate outcome still requires the subsequent reviewed assessment.

## Required local checks

From `backend/`:

```bash
uv sync --locked --python 3.13
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
uv audit --locked
docker build --tag afyaher-backend:local .
```

From `frontend/`:

```bash
npm ci --no-audit --no-fund
npm run lint
npm run format:check
npm run typecheck
npm run test
npm run build
npm audit --audit-level=high
docker build --tag afyaher-frontend:local .
```

From a full checkout, also install the matching Playwright browser with
`npx playwright install --with-deps chromium` and run `npm run test:e2e` in
`frontend/`. Playwright starts the local backend and frontend. Stop only your own
development servers if they occupy ports 8000/3000. Use synthetic questions only;
review logs/screenshots before sharing. Run builds/type generation and development
servers sequentially against the same `.next` folder.

Use `ruff format` / `npm run format` deliberately on touched files. Do not hide
new failures, add `continue-on-error`, skip security checks or use `npm audit fix
--force` to make CI green. Report infrastructure/network failures separately.
Security exceptions require an owner, rationale, risk assessment and expiry; no
exception is configured by default. Dependency updates remain reviewed PRs.

## Root and frontend repositories

`frontend/` is a separate Git repository recorded by the root project's Git link.
`.gitmodules` now records its real remote. Clone with `--recurse-submodules` or
run `git submodule update --init` in an authorized full clone.

Commit and push frontend changes to `winniekagz/frontend` first. Then commit the
updated `frontend` Git link in `winniekagz/afyaher`. Root CI checks the exact
recorded frontend commit, never a moving branch. Unpushed frontend commits cannot
be checked out by GitHub runners. Do not flatten or reinitialize either history.
See [CI setup](docs/CI.md) for private-repository credentials and required checks.

## Review and release

PRs must state changed behavior, relevant requirements, exact validation commands
and results, remaining risks, and any approved contract/dependency changes. Request
an independent reviewer for safety/security/content/approval-policy changes.
Configure branch protection to enforce CI and review; merely committing workflow
or CODEOWNERS files does not enable that enforcement.

Do not deploy, ingest medical content or enable generated medical answers as a
side effect of routine CI/build work. All clinical, privacy, security and applicable
legal release gates remain in force. See [SECURITY.md](SECURITY.md).
