# Local Typesense setup

Typesense is an internal backend service (official server image 30.2). Never place its admin key in
`NEXT_PUBLIC_*` configuration or frontend code.

## Configure and start

1. Copy `backend/.env.example` to the ignored `backend/.env` file if needed
   (use `cp -n backend/.env.example backend/.env` to preserve an existing file).
2. Generate a private local development key, for example with
   `openssl rand -hex 32`, and set it as `TYPESENSE_API_KEY` in
   `backend/.env`. Keep the key out of Git and chat.
3. Start the Compose stack with `docker compose --env-file backend/.env up -d
   --build`. Typesense listens on `127.0.0.1:8108`; FastAPI uses the service
   hostname internally. The key is passed only to the Typesense service and
   backend container.
4. Check `docker compose ps` and `curl http://127.0.0.1:8108/health`.

For a backend running directly on the host, leave `TYPESENSE_HOST=localhost`
in `backend/.env` and use `cd backend && uv run ...`.

## Create the collection and index

The collection schema is versioned in code. The index command creates it if
absent and refuses an incompatible existing schema:

```sh
cd backend
uv run python -m scripts.index_approved_passages
```

The checked-in `backend/data/approved/passages.json` is intentionally empty.
The command therefore reports that there is nothing eligible to index. Add
only passage records with actual review approval and source permission. The
command skips pending/rejected records and sources that fail existing
eligibility rules. It does not fetch websites or create medical content.

Search the API with synthetic text only:

```sh
curl -sS -X POST http://127.0.0.1:8000/api/v1/knowledge/search \
  -H 'Content-Type: application/json' \
  -d '{"topic":"pcos","question":"A synthetic test question"}'
```

No answer is generated. Candidate results have unassessed evidence
sufficiency. No result means abstention; a Typesense failure returns a safe
503 response.

## Tests and troubleshooting

```sh
cd backend
uv run pytest tests/test_typesense_knowledge.py
uv run pytest
```

If the API reports `retrieval_unavailable`, check Typesense health, the
collection creation command, and that the backend and Typesense use the same
local API key. Do not work around an outage by switching to synthetic fixtures
or the local keyword retriever for production retrieval.

This local setup is a private demonstration configuration, not a production
security deployment.
