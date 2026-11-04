# AfyaHer API and Swagger documentation

The current API has two application endpoints. Documentation is generated from
the FastAPI routes and existing Pydantic models; no separate Swagger service or
new dependency is needed.

From `backend/`, start the local API:

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open:

| Documentation | Local URL |
| --- | --- |
| Interactive Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |
| Live OpenAPI JSON | http://127.0.0.1:8000/openapi.json |

The URLs above assume the default port. Use your configured backend port for a
Compose override. The documentation pages use FastAPI's default externally hosted
Swagger/ReDoc UI assets; they may require internet access to render. The live JSON
and [checked-in schema](openapi.json) can be read without those UI assets.

Use synthetic input only, including Swagger's **Try it out** action. No API key
or account is required for this local prototype. CORS and documentation notices
are not authentication. Keep the backend on loopback; no public deployment or
clinical approval is implied.

## Endpoints

| Method and path | Success behavior | Validation/failure behavior |
| --- | --- | --- |
| `GET /api/v1/health` | HTTP 200, `{"status":"ok","service":"afyaher-api"}`, `Cache-Control: no-store` | Unsupported methods return 405. Liveness only, not database, evidence, AI, or clinical readiness |
| `POST /api/v1/education/ask` | HTTP 200 with application status `service_unavailable`, empty `sources`, and fixed limitation/disclaimer | Invalid request returns framework 422; unsupported methods return 405. No answer generation, symptom screening, retrieval or medical evidence assessment is connected |

The education request accepts only:

- `topic`: `pcos`, `ovarian-cysts`, or `ovarian-torsion`.
- `question`: string, trimmed before validation; at least three non-whitespace
  characters and at most 2,000 total characters after trimming.

Missing/extra fields, unsupported topics, wrong question types and invalid lengths
are rejected. Current framework validation errors can echo input values; valid
responses also echo the normalized question. Education responses currently have
no explicit no-store header. Do not use real health questions or identifying data
in this prototype or documentation tooling. These limitations are tracked in the
[audit](../audits/AFYAHER_GAP_ANALYSIS.md).

Synthetic example:

```bash
curl --request POST http://127.0.0.1:8000/api/v1/education/ask \
  --header 'Content-Type: application/json' \
  --data '{"topic":"pcos","question":"A synthetic educational question for testing."}'
```

Actual response:

```json
{
  "status": "service_unavailable",
  "topic": "pcos",
  "question": "A synthetic educational question for testing.",
  "answer": "Educational answers are not available yet.",
  "sources": [],
  "limitations": "The evidence-backed answer service is not implemented.",
  "disclaimer": "This is educational information, not medical advice. Consult a qualified clinician for personal health decisions."
}
```

`service_unavailable` is an application outcome inside HTTP 200, **not HTTP 503**.
The response schema also lists `answered`, `insufficient_evidence`,
`clarification_needed`, `out_of_scope`, and `urgent_guidance`; those values are
reserved in the contract and are not produced by the current stub. The endpoint
cannot assess or rule out an emergency.

## Maintain and verify the documentation

From `backend/`:

```bash
uv run python -m scripts.export_openapi
uv run pytest tests/test_openapi.py -q
```

The exporter writes `docs/api/openapi.json` deterministically from `create_app()`
without starting a server, reading a local `.env`, fetching sources, or calling a
model. `--out PATH` can write another copy. Commit the regenerated schema with
route/model documentation changes.

Tests check that Swagger and ReDoc reference the live schema, the checked-in
schema matches the running app, documented synthetic examples produce exactly
the actual unavailable response, and export is reproducible. The docs introduce
no new application endpoints or public request/response fields.

Verified on 4 November 2026: `.venv/bin/pytest -q` passed 319 tests (one existing
Starlette/HTTPX warning); `npm run test` from `frontend/` passed 37 tests.
`.venv/bin/ruff check .` and formatting checks on the five changed Python files
passed. Existing unrelated formatting failures and the missing Playwright browser
revision are recorded in the current-state audit; this documentation task does
not claim to resolve those findings.
