# Starting the PCOS knowledge base

Use the [source catalogue](PCOS_SOURCE_CATALOGUE.md) to decide what can lawfully
be ingested and reviewed. Start with deterministic source acquisition and the
existing lexical passage search. A model's remembered facts are not retrieved
evidence and must never become source text or approval metadata.

The approved hosted free-tier experiment uses OpenRouter to select passage IDs
from an existing synthetic candidate batch. This is a developer CLI, independent
of `/education/ask`; it does not fetch medical pages, create a medical knowledge
base, assess clinical sufficiency or generate medical answers. It currently
refuses all non-synthetic sources, including approved-looking fictional records.

## Try the local preview

From `backend/`, with the existing environment installed:

```bash
.venv/bin/python -m scripts.inspect_sources
.venv/bin/python -m scripts.search_passages_with_llm 'green lanterns'
```

The second command performs only lexical retrieval over committed non-clinical
fixtures. It prints selected IDs and counts, without echoing the query or passage
text. There is no network request, persistence or LLM call in this mode.

## Configure an optional hosted experiment

1. Review OpenRouter's [privacy policy and data handling](https://openrouter.ai/docs/guides/privacy/data-collection),
   [free variants](https://openrouter.ai/docs/guides/routing/model-variants/free),
   [limits](https://openrouter.ai/docs/api_reference/limits), and
   [provider-routing controls](https://openrouter.ai/docs/guides/routing/provider-selection).
   Review the actual selected provider's terms and endpoint capabilities too.
   A free price does not establish permission, clinical suitability or privacy.
2. Obtain a separate application research key. Configure these variables privately
   in the shell/secret environment used by the CLI:
   `AFYAHER_RESEARCH_API_KEY`, `AFYAHER_RESEARCH_MODEL`, and
   `AFYAHER_RESEARCH_PROVIDER`. Use a specific current `vendor/model:free` ID and
   the reviewed provider slug. The CLI does not automatically load `.env`.
   Never paste keys into chat, tracked files, command examples or browser settings.
3. To inspect the public zero-price catalogue without a key, query or inference:

   ```bash
   .venv/bin/python -m scripts.search_passages_with_llm --list-free-models
   ```

4. After provider review and private configuration, explicitly opt into sending
   synthetic data for this invocation:

   ```bash
   .venv/bin/python -m scripts.search_passages_with_llm 'green lanterns' --live --confirm-synthetic-data
   ```

Only use fictional queries. The source corpus is fixed to synthetic fixtures, but
the CLI cannot determine whether text typed by a person is sensitive. Synthetic
queries on the command line can appear in local shell history/process listings.
There are no real-user questions or medical excerpts in the current experiment.

No specific live model/provider combination has been validated. The public model
catalogue is not a provider availability or terms approval. Free endpoints may
not satisfy all configured controls; a failed request should remain a failure.
Do not weaken the controls or introduce a paid fallback to make a demo work.

## Boundaries and validation

`app/services/research_retrieval.py` uses the standard library and existing
schemas. It validates the entire candidate batch, bounds input and response sizes,
uses a 15-second socket timeout, refuses redirects, and makes no retries. It checks
the current catalogue for zero prices, fixes one model and provider, disables
fallbacks, requests zero maximum prices, requires supported parameters, denies
provider data collection, and requests ZDR routing. It accepts only a zero-cost
response containing unique, previously retrieved IDs, then returns original
passage records. Invented IDs, generated prose and malformed responses fail.

These are request controls, not a contractual guarantee of no retention or billing:
OpenRouter documents account logging settings and safety/legal exceptions. A
response cost check is retrospective. No paid service call is authorized by this
experiment; recheck provider terms, account settings and spending limits before
any invocation. A socket timeout is not an overall wall-clock deadline.

The model can still select irrelevant original passages or omit useful ones.
Successful parsing establishes neither relevance nor clinical support. Lexical
retrieval remains the baseline; future retrieval evaluation should compare both
approaches on fixed synthetic relevance judgments before considering medical data.

The next milestone is source rights/review evidence and versioned acquisition for
one source, followed by passage-level relevance evaluation. Claim-support
assessment and answer generation remain separate, unimplemented milestones.

Canonical `docs/PRD.md`, `docs/ARCHITECTURE.md` and `docs/SYSTEM_DESIGN.md` remain
missing. Root Word drafts are available; they do not replace an approved system
design. Source specifications are still needed for those canonical documents.
