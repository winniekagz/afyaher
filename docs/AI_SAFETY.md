# AI and evidence safety boundary

There is no AI answer generation in the Typesense retrieval phase.

Only passages with an explicit passage-level approval record and a source that
passes existing permission, source-review, production-scope, and
non-synthetic checks may be indexed. Search results are checked again against
the current passage approval manifest, source metadata, and content hashes
before being returned. Re-indexing removes stale passages after approval is
revoked. An unapproved, unknown, tampered, or wrong-topic passage is never
returned.

Retrieval-level evidence is only a candidate set. Typesense ranking does not
prove that a passage supports a medical statement. Therefore a non-empty search
response reports `evidence_sufficiency: not_assessed` and must not be presented
as a validated answer. Empty retrieval abstains. Retrieval failures also
abstain and never trigger a less restrictive fallback.

No source or passage may be marked approved by automation. The registry and
passage review data currently contain no production-eligible PCOS content, and
the other initial topics have no source registry. Do not invent content to
populate the index. Clinical reviewers must establish the real approval and
permission records before indexing any medical passage.

This prototype is not clinically validated or ready for public patient use.
It must not diagnose, assess symptoms, recommend treatment, or perform
emergency triage. A future answer-generation phase needs independent
claim-to-evidence validation, deterministic safety screening, citation
validation, and clinical review before streamed answer text can be displayed.
