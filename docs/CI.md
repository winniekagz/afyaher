# GitHub Actions setup and verification

## What is configured

| Repository / workflow | Checks |
| --- | --- |
| Root `.github/workflows/backend.yml` | Locked uv/Python 3.13 setup; Ruff lint/format, pytest including Swagger schema drift, backend Docker build, `uv audit --locked` |
| Root `.github/workflows/frontend.yml` | Exact Git-linked frontend checkout; Node 22/npm lock install; ESLint/Prettier/TypeScript/Vitest, production and Docker builds, matching Chromium installation, backend-connected Playwright, npm high/critical audit |
| Frontend `.github/workflows/ci.yml` | Standalone frontend lint/format/type/unit/build/Docker/audit; no backend assumed in a frontend-only clone |

Root browser CI runs `node .next/standalone/server.js` when `CI` is
set, rather than letting development Fast Refresh reset in-memory journeys.
Ordinary local browser runs retain `npm run dev`; to reproduce CI locally, build
first, copy the public/static assets as shown below, and run `CI=true npm run test:e2e`:

```bash
cp -R public .next/standalone/
cp -R .next/static .next/standalone/.next/
CI=true npm run test:e2e
```

All run on `main` pushes, pull requests and manual dispatch, without path filters
that could strand required checks. Jobs have finite timeouts, read-only contents,
no persisted checkout credentials, no package caches and no publishing/deployment.
Cancelling obsolete runs prevents duplicate branch work. Action hashes were
resolved from the official repositories' v6 checkout/setup-node and v7 setup-uv
references during implementation; uv is pinned to the existing 0.11.9 tool version.
No application dependency or public API changes are introduced.

The dependency audit identified critical advisories in the old Vitest/tinypool
test stack. With explicit user approval, Vitest was upgraded to 4.1.12 and its
configuration migrated to `vitest.config.mts` with the current JSX transform.
Existing production package versions were unchanged. The follow-up audit has no
high/critical findings, with 16 moderate ESLint/minimatch-chain advisories still
requiring triage; the gate was not silenced or force-fixed.

Dependency audits are gates, not proofs of safety. npm high/critical failures and
uv advisory failures need review; network/advisory-service failures are not passes.
Dependency updates are proposed weekly through Dependabot: root actions/uv/backend
Docker/submodule, frontend actions/npm/Docker. Root Dependabot cannot edit the
separate frontend repository's lockfile; its own configuration handles that.

## Required repository-owner setup

1. Commit/push frontend changes first, then the root Git link and workflows.
   The linked revision must exist remotely. These files do not run until pushed;
   no GitHub-hosted run is claimed from local validation.
2. For a public frontend repository, normal GitHub checkout permissions suffice.
   If `winniekagz/frontend` is private, add root Actions secret
   `FRONTEND_READ_TOKEN` using a fine-grained token with only that repository's
   contents read permission. Never paste it into source or chat. The root repo's
   default token alone normally cannot read a separate private repository.
3. The token is used only in the checkout action with persistence disabled. Fork
   PRs/Dependabot contexts may lack the secret; the checkout then fails closed
   rather than running privileged PR code. A maintainer must use an approved
   internal branch/review process for private-source contributions. Do not switch
   to `pull_request_target` to bypass this restriction.
4. Enable branch protection/rulesets after the first runs register their checks.
   Require the root **Backend quality** and **Frontend quality and integration**
   checks; require **Frontend quality** in the frontend repository. Require PRs,
   resolved discussions and appropriate independent review for safety/security
   changes. CODEOWNERS names the actual repository owner; add a qualified reviewer
   before enforcing independent approvals on that owner's own PRs.
5. Enable Dependabot alerts and secret scanning/push protection where supported;
   restrict allowed action sources and require pinned references. These server
   settings are not changed by adding YAML/CODEOWNERS files.

Root checkout deliberately reads `git rev-parse HEAD:frontend` and passes that
commit to a separate checkout of the fixed frontend repository. It never builds
an unrelated moving frontend branch. `.gitmodules` repairs ordinary recursive
clone metadata without flattening the repositories or rewriting history.

## Local checks and build

Use the exact commands in [CONTRIBUTING.md](../CONTRIBUTING.md). For both existing
images from the root:

```bash
docker compose config --quiet
docker compose build
```

Building images does not start services or expose ports. No registry push or
deployment is configured. Browser installation is test-environment setup, not a
production dependency; use the version selected by the locked Playwright package.

## Reference guidance

The workflow permission, immutable-action and untrusted-PR choices follow
[GitHub's secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use).
Dependency update configuration follows
[uv's Dependabot integration](https://docs.astral.sh/uv/guides/integration/dependabot/)
and [GitHub's supported ecosystems](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories).
Actual local checks and build outcomes are recorded in `CI_VERIFICATION.md` after
execution. Configuring these controls does not resolve the clinical/privacy
release blockers in the audit.
