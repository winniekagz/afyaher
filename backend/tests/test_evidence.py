"""Provenance tests using fictional metadata and non-clinical prose only."""

import builtins
import io
import logging
import os

import pytest
from pydantic import ValidationError

from app.schemas.educational import Topic
from app.schemas.knowledge import KnowledgeSource, RetrievedPassage, SourceRegistry
from app.services.evidence import EvidenceResult, EvidenceStatus, assess_provenance
from app.services.knowledge import SYNTHETIC_DIR, load_registry
from app.services.retrieval import load_passage_sets, retrieve
from tests.test_knowledge import ELIGIBLE, make_source


def source(**overrides) -> KnowledgeSource:
    return KnowledgeSource.model_validate(make_source(**(ELIGIBLE | overrides)))


def record(**overrides) -> RetrievedPassage:
    passage = {
        "id": "example-source-p0",
        "source_id": "example-source",
        "topic": "pcos",
        "position": 0,
        "text": "The fictional archive stores copper lanterns.",
    }
    return RetrievedPassage(
        passage=passage | overrides, score=1, matched_terms=["lanterns"]
    )


def registry(*sources: KnowledgeSource) -> SourceRegistry:
    return SourceRegistry(topic=Topic.PCOS, sources=list(sources))


def test_empty_retrieval_returns_no_evidence():
    result = assess_provenance(Topic.PCOS, [], registry(source()))
    assert result.status is EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert result.candidates == ()


def test_synthetic_with_fictional_approval_metadata_is_rejected():
    fixture = source(
        evidence_type="synthetic_fixture", content_scope="development_only"
    )
    result = assess_provenance(Topic.PCOS, [record()], registry(fixture))
    assert result.status is EvidenceStatus.INVALID_EVIDENCE
    assert result.candidates == ()


@pytest.mark.parametrize(
    "overrides",
    [
        {"content_scope": "development_only"},
        {"ingestion_permission": "not_verified"},
        {"ingestion_permission": "prohibited"},
        {"clinical_review_status": "not_reviewed"},
        {"clinical_review_status": "in_review"},
        {"clinical_review_status": "rejected"},
    ],
)
def test_ineligible_sources_reject_the_entire_batch(overrides):
    result = assess_provenance(Topic.PCOS, [record()], registry(source(**overrides)))
    assert result.status is EvidenceStatus.INVALID_EVIDENCE
    assert result.candidates == ()


@pytest.mark.parametrize(
    "field", ["license", "authorization_reference", "authorization_date"]
)
def test_missing_permission_evidence_cannot_bypass_policy(field):
    # Deliberately bypass source validation to exercise the existing policy's
    # defensive checks. No real approval metadata is changed.
    incomplete = source().model_copy(update={field: None})
    sources = registry(source()).model_copy(update={"sources": [incomplete]})
    result = assess_provenance(Topic.PCOS, [record()], sources)
    assert result.status is EvidenceStatus.INVALID_EVIDENCE
    assert result.candidates == ()


@pytest.mark.parametrize(
    "overrides",
    [
        {"id": "unknown-p0", "source_id": "unknown"},
        {"topic": "ovarian-cysts"},
        {"id": "example-source-p7"},
        {"position": 7},
    ],
)
def test_inconsistent_passages_are_rejected(overrides):
    result = assess_provenance(Topic.PCOS, [record(**overrides)], registry(source()))
    assert result.status is EvidenceStatus.INVALID_EVIDENCE
    assert result.candidates == ()


@pytest.mark.parametrize("position", [-1, 1.5, True])
def test_invalid_positions_are_revalidated(position):
    item = record()
    item.passage = item.passage.model_copy(update={"position": position})
    result = assess_provenance(Topic.PCOS, [item], registry(source()))
    assert result.status is EvidenceStatus.INVALID_EVIDENCE
    assert result.candidates == ()


def test_requested_topic_must_match_registry_and_passages():
    result = assess_provenance(Topic.OVARIAN_CYSTS, [record()], registry(source()))
    assert result.status is EvidenceStatus.INVALID_EVIDENCE
    assert result.candidates == ()


def test_passage_topic_must_match_its_source():
    result = assess_provenance(
        Topic.OVARIAN_CYSTS, [record(topic="ovarian-cysts")], registry(source())
    )
    assert result.status is EvidenceStatus.INVALID_EVIDENCE
    assert result.candidates == ()


def test_duplicate_ids_reject_the_entire_batch():
    result = assess_provenance(Topic.PCOS, [record(), record()], registry(source()))
    assert result.status is EvidenceStatus.INVALID_EVIDENCE
    assert result.candidates == ()


@pytest.mark.parametrize("invalid_first", [False, True])
def test_mixed_batch_never_returns_partial_evidence(invalid_first):
    items = [record(), record(id="ghost-p0", source_id="ghost")]
    if invalid_first:
        items.reverse()
    result = assess_provenance(Topic.PCOS, iter(items), registry(source()))
    assert result.status is EvidenceStatus.INVALID_EVIDENCE
    assert result.candidates == ()


def test_valid_candidates_require_support_assessment_and_keep_retrieval_order():
    # Ranked retrieval subsets need not start at zero or be consecutive.
    items = [record(id="example-source-p9", position=9), record()]
    result = assess_provenance(Topic.PCOS, iter(items), registry(source()))
    assert result.status is EvidenceStatus.SUPPORT_ASSESSMENT_REQUIRED
    assert result.candidates == tuple(item.passage for item in items)
    assert not hasattr(result, "can_generate")


@pytest.mark.parametrize("score", [1, 10, 1000000])
def test_high_scoring_irrelevant_fiction_never_authorizes_an_answer(score):
    item = record(text="The imaginary north room is painted violet.")
    item.score = score
    result = assess_provenance(Topic.PCOS, [item], registry(source()))
    assert result.status is EvidenceStatus.SUPPORT_ASSESSMENT_REQUIRED
    assert "score" not in type(result.candidates[0]).model_fields


def test_default_production_retrieval_of_synthetic_content_abstains():
    sources = load_registry(SYNTHETIC_DIR / "registry.json")
    passage_sets = load_passage_sets(SYNTHETIC_DIR / "passages")
    items = retrieve("green lanterns", Topic.PCOS, sources, passage_sets)
    assert items == []
    result = assess_provenance(Topic.PCOS, items, sources)
    assert result.status is EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert result.candidates == ()


def test_candidates_are_snapshots_and_inputs_are_unchanged():
    item = record()
    sources = registry(source())
    before = item.model_dump(), sources.model_dump()
    result = assess_provenance(Topic.PCOS, [item], sources)
    assert (item.model_dump(), sources.model_dump()) == before
    item.passage.text = "An edited fictional ledger."
    assert result.candidates[0].text != item.passage.text


@pytest.mark.parametrize("invalid", [False, True])
def test_gate_does_not_log_print_or_access_files(monkeypatch, caplog, capsys, invalid):
    item = record(source_id="unknown") if invalid else record()
    sources = registry(source())

    def forbid_file_access(*args, **kwargs):
        pytest.fail("The provenance gate must not access files")

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", forbid_file_access)
        patch.setattr(io, "open", forbid_file_access)
        patch.setattr(os, "open", forbid_file_access)
        with caplog.at_level(logging.DEBUG):
            result = assess_provenance(Topic.PCOS, [item], sources)

    assert result.status is (
        EvidenceStatus.INVALID_EVIDENCE
        if invalid
        else EvidenceStatus.SUPPORT_ASSESSMENT_REQUIRED
    )
    assert caplog.records == []
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_result_contract_has_exactly_three_outcomes():
    assert {status.value for status in EvidenceStatus} == {
        "insufficient_evidence",
        "invalid_evidence",
        "support_assessment_required",
    }


@pytest.mark.parametrize(
    "status", [EvidenceStatus.INSUFFICIENT_EVIDENCE, EvidenceStatus.INVALID_EVIDENCE]
)
def test_rejected_results_cannot_contain_candidates(status):
    with pytest.raises(ValidationError):
        EvidenceResult(status=status, candidates=(record().passage,))


def test_support_assessment_outcome_requires_candidates():
    with pytest.raises(ValidationError):
        EvidenceResult(status=EvidenceStatus.SUPPORT_ASSESSMENT_REQUIRED)
