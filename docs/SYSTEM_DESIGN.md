# Knowledge retrieval system design

## Passage lifecycle

1. A source is discovered and registered with publisher, URL, topic,
   permission, and source review metadata.
2. Passage workflow records distinguish `retrieved`, `processed`,
   `pending_review`, `approved`, and `rejected`. Content is obtained only
   through a separately permitted process; this
   repository does not scrape or download publisher pages.
3. A human curated passage record is written to
   `backend/data/approved/passages.json` with source ID, topic, section, text,
   publication date, passage review status, approval timestamp, and reviewer
   qualification.
4. The index command validates each record and the matching source registry.
   Pending, rejected, and unapproved-source passages are skipped. Invalid
   records are reported without printing passage text.
5. Approved eligible passages are upserted by deterministic ID. The ID is
   derived from source, topic, section, and content hash; re-indexing changed
   text creates a new ID. `content_hash` is SHA-256 over the passage text.
6. Typesense represents the `indexed` lifecycle state by the presence of the
   approved record in the versioned collection. Search also filters
   `approval_status=approved`. Re-indexing reconciles the collection against
   the current approved manifest and deletes records whose approval was
   removed or whose content changed.

Passage approval and source-level permission/review are independent gates. A
source's presence in the registry does not approve its passages. Do not enter
an approved review record unless a qualified reviewer has actually completed
that review and permission to process the content is documented.

## Collection

`afyaher_knowledge_v2` has faceted `topic`, `source_id`, and
`approval_status`; full-text `passage`; traceability fields for source title,
URL, and section; optional publication date; approval timestamp; and content
hash. Search is restricted by exact topic and approved status. The collection
name versions the schema. A conflicting schema under the same name fails
closed.

## Retrieval and abstention

`POST /api/v1/knowledge/search` accepts the existing validated `topic` and
`question` plus a bounded result limit. It returns one of:

- `candidates_found`: topic-filtered, source-validated candidates were found;
  sufficiency remains `not_assessed`.
- `no_matching_evidence`: the search produced no eligible passage;
  sufficiency is `insufficient`.
- `retrieval_unavailable`: Typesense, source metadata, or indexed provenance
  could not be checked; the endpoint returns HTTP 503 with no passage content.

Every result is checked against the current passage approval manifest, source
registry, source eligibility, topic, approval marker, content hash, and
deterministic passage ID. Search
ranking is not a confidence score and does not establish that a passage
supports a medical claim. This phase returns no answer text.

## Failure handling

Missing API key, Typesense downtime, malformed search results, invalid source
metadata, or inconsistent indexed records fail closed. The API emits a generic
unavailable status. It does not fall back to development fixtures or
keyword-only production retrieval. User questions are processed in memory and
are not stored or logged by this service.
