# Security and medical-safety standards

AfyaHer is a private prototype, not a clinically validated patient service.
Security controls and test results do not establish medical safety or compliance.

## Reporting

Use GitHub's private vulnerability reporting feature if enabled for this repository,
or contact the repository owner through an established private channel. Do not
post credentials, patient information, raw health questions or exploit payloads
containing personal data in public issues. There is no asserted response-time SLA
or dedicated clinical incident service. Only the current development branch is
maintained; no production release support is claimed.

## Development controls

- Use synthetic data. No persistent chat history, medical-record uploads, raw
  health-question logs, analytics or sensitive screenshots by default.
- Keep keys server-side in ignored local environment files or an approved secret
  store. Never put them in client bundles, prompts, workflow files or fixtures.
  Separate coding-agent credentials/budgets from application runtime credentials.
- Validate request types, sizes and response schemas. Use bounded timeouts/retries,
  explicit failure statuses and fail-closed evidence checks. Avoid raw input in
  errors and telemetry. The existing API privacy gaps are tracked in the audit;
  this standards file does not claim they are repaired.
- Preserve production permission/review/scope gates and development-fixture
  isolation. Treat source text and user input as data, never trusted instructions.
- Never implement diagnosis, symptom-based clinical triage, treatment selection,
  prescriptions, dosing or fertility prediction. Reviewed urgent-risk interruption
  is not a reliable emergency rule-out system.
- Maintain restrictive local CORS, loopback demo ports and non-root containers.
  CORS, robots metadata and notices are not authentication or deployment approval.
- Review lockfile updates and dependency advisories. CI runs `uv audit --locked`
  and fails npm audits at high/critical severity; lower npm findings still require
  triage. Audits contact public advisory services with dependency metadata only.
  Never send user questions or source contents to those services.
- No dependency auto-fix, auto-merge, workflow publication, image push, deployment,
  or database migration is part of the CI configuration.

## Workflow trust

Use full verified action commit hashes, read-only contents permissions, finite
timeouts and `persist-credentials: false`. Do not run untrusted PR code with
`pull_request_target`, write tokens, cloud credentials or production secrets.
The optional cross-repository checkout token must be read-only for the frontend
repository and must not be reused for deployment or runtime APIs. Fork PRs do not
receive it; a private frontend checkout may therefore fail explicitly.

Enable repository secret scanning/push protection and dependency alerts where
available, restrict action sources, and require branch checks/review in GitHub
settings. These settings require repository-owner configuration and were not
enabled or verified by editing these files. Do not report pattern scans or
dependency audits as a complete security assessment.

## Release gates

Before any external use: qualified review of medical content and escalation rules,
documented source authorization and review evidence, privacy/retention and security
review, access controls/rate/body limits, claim-support and output evaluations,
incident/rollback arrangements and applicable legal/regulatory review. Backend
medical generation remains unavailable until those approved contracts are ready.

If a credential is exposed, stop using it, revoke/rotate it through the owning
service, assess affected access and remove exposed artifacts with explicit review.
Do not rewrite history, delete data or disable security checks without authorization.
