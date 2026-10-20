# Day 1 implementation agreement

Approved scope: a running Next.js UI communicating directly from the browser with a running FastAPI backend through `GET /api/v1/health`. Include loading, success, error, retry, strict response validation, restrictive local CORS, reproducible dependencies, and essential tests.

The user subsequently requested Dockerization and running both services. Add only frontend/backend images and Compose, publish ports on host loopback, and verify the running containers. This does not add database or AI infrastructure.

Preserve the modular-monolith boundary. Next.js owns presentation. FastAPI owns business logic, safety, evidence, and AI when those features are added later. No medical advice, RAG, generation, authentication, database infrastructure, or paid API calls on Day 1.

## Decisions

- Preserve the existing Next.js App Router and dependency versions. Replace experimental starter CSS configuration with Tailwind's PostCSS integration; omit unrelated caching/prefetch options for the connection slice.
- Use system fonts so builds do not fetch external font assets.
- Use Next.js's supported `--webpack` option for development and builds. Turbopack's PostCSS worker failed to bind an internal port in this managed environment, including an unrestricted retry. This changes the bundler only, not the application architecture.
- Use npm/package-lock for the frontend and uv/uv.lock for the backend. Select the installed Python 3.13 runtime. No global Python packages are installed.
- Keep the health route and response schema small; do not create speculative services, repositories, or database layers.
- Call FastAPI from the browser with a five-second timeout and no cookies. This verifies the actual browser network/CORS boundary. No Next.js proxy or API route is needed.
- Bind both development servers to 127.0.0.1. Local-only operation is the privacy boundary for Day 1; notices and robots metadata are not security controls.
- The 18+ notice states the intended adult audience. There is no account or identity verification.
- Preserve the legitimate AGENTS guidance through its final first-task instruction and remove only the unrelated copied browser-data suffix. Append the approved Day 1 agreement to all three instruction files. Copilot follows CLAUDE.md's full standards.

## Missing specifications

`docs/PRD.md`, `docs/ARCHITECTURE.md`, and `docs/SYSTEM_DESIGN.md` were not present. Obtain/import the existing MVP documents before broader feature work and resolve any conflict with the current instructions. This file records implementation decisions, not an invented approved PRD.

## Verification goals

Backend tests cover HTTP contract, schema rejection, CORS allowlist, rejected preflight, and unsupported methods. Frontend units cover payload validation, failures, loading/success, retry, and abort on unmount. Playwright starts both servers and checks real browser connectivity in a mobile viewport, error recovery, and timeout. Run lint, formatting, TypeScript checks, and production build, and record actual results in DAY1_VERIFICATION.md.

## Next sprint step

Start Day 2 by reconciling the existing PRD and defining the PCOS education slice's acceptance criteria. Agree source provenance/review status and safety/abstention contracts before implementing medical content or model calls. Keep the prototype private and synthetic pending clinical, privacy, security, and regulatory reviews. Database and AI dependencies should be added only with the next approved slice.
