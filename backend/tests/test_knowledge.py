"""Tests for the source registry schemas, eligibility rule, and inspection script.

All records are synthetic metadata; no medical content is used.
"""

import json
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.knowledge import (
    ClinicalReviewStatus,
    IngestionPermission,
    KnowledgeSource,
    SourceRegistry,
)
from app.services.knowledge import SOURCES_DIR, is_eligible_for_ingestion, load_registry
from scripts.inspect_sources import main as inspect_main


def make_source(**overrides) -> dict:
    source = {
        "id": "example-source",
        "topic": "pcos",
        "title": "Example source",
        "publisher": "Example Publisher",
        "url": "https://example.org/pcos",
        "evidence_type": "fact_sheet",
        "content_scope": "production",
        "publication_date": None,
        "last_verified_date": None,
        "clinical_review_status": "not_reviewed",
        "ingestion_permission": "not_verified",
        "license": None,
        "authorization_reference": None,
        "authorization_date": None,
        "ingestion_status": "metadata_only",
    }
    source.update(overrides)
    return source


def make_registry(*sources: dict) -> dict:
    return {"topic": "pcos", "sources": list(sources) or [make_source()]}


def write_registry(tmp_path, data) -> str:
    path = tmp_path / "registry.json"
    path.write_text(data if isinstance(data, str) else json.dumps(data))
    return str(path)


ELIGIBLE = {
    "ingestion_permission": "permitted",
    "license": "Synthetic test license",
    "authorization_reference": "https://example.org/license",
    "authorization_date": "2026-01-01",
    "clinical_review_status": "approved",
}


# ── Schema validation ─────────────────────────────────────────────


class TestKnowledgeSource:
    def test_valid_source(self):
        source = KnowledgeSource.model_validate(make_source())
        assert source.ingestion_permission is IngestionPermission.NOT_VERIFIED
        assert source.publication_date is None

    def test_parses_verified_dates(self):
        source = KnowledgeSource.model_validate(
            make_source(publication_date="2023-08-01", last_verified_date="2026-11-02")
        )
        assert source.publication_date == date(2023, 8, 1)

    @pytest.mark.parametrize(
        "url", ["ftp://example.org/pcos", "not-a-url", "javascript:alert(1)", ""]
    )
    def test_rejects_invalid_url(self, url):
        with pytest.raises(ValidationError):
            KnowledgeSource.model_validate(make_source(url=url))

    @pytest.mark.parametrize(
        "field",
        [
            "id",
            "title",
            "publisher",
            "url",
            "publication_date",
            "license",
            "authorization_reference",
            "authorization_date",
            "ingestion_permission",
        ],
    )
    def test_rejects_missing_required_field(self, field):
        data = make_source()
        del data[field]
        with pytest.raises(ValidationError, match=field):
            KnowledgeSource.model_validate(data)

    @pytest.mark.parametrize("field", ["id", "title", "publisher"])
    @pytest.mark.parametrize("value", ["", "   "])
    def test_rejects_blank_strings(self, field, value):
        with pytest.raises(ValidationError):
            KnowledgeSource.model_validate(make_source(**{field: value}))

    @pytest.mark.parametrize("source_id", ["Who PCOS", "who_pcos", "-who", "who-"])
    def test_rejects_non_slug_id(self, source_id):
        with pytest.raises(ValidationError):
            KnowledgeSource.model_validate(make_source(id=source_id))

    def test_rejects_unsupported_topic(self):
        with pytest.raises(ValidationError, match="topic"):
            KnowledgeSource.model_validate(make_source(topic="endometriosis"))

    @pytest.mark.parametrize(
        "field",
        [
            "evidence_type",
            "clinical_review_status",
            "ingestion_permission",
            "ingestion_status",
        ],
    )
    def test_rejects_invalid_status_value(self, field):
        with pytest.raises(ValidationError, match=field):
            KnowledgeSource.model_validate(make_source(**{field: "approvedd"}))

    def test_rejects_unexpected_field(self):
        with pytest.raises(ValidationError, match="content"):
            KnowledgeSource.model_validate(make_source(content="copied article text"))

    @pytest.mark.parametrize(
        "field", ["license", "authorization_reference", "authorization_date"]
    )
    def test_permitted_requires_authorization_evidence(self, field):
        with pytest.raises(ValidationError, match=field):
            KnowledgeSource.model_validate(make_source(**{**ELIGIBLE, field: None}))

    def test_legacy_source_defaults_to_development_only(self):
        data = make_source()
        del data["content_scope"]
        source = KnowledgeSource.model_validate(data)
        assert source.content_scope == "development_only"

    def test_rejects_invalid_content_scope(self):
        with pytest.raises(ValidationError, match="content_scope"):
            KnowledgeSource.model_validate(make_source(content_scope="staging"))

    def test_synthetic_fixture_must_be_development_only(self):
        with pytest.raises(ValidationError, match="development_only"):
            KnowledgeSource.model_validate(
                make_source(
                    evidence_type="synthetic_fixture", content_scope="production"
                )
            )

    def test_real_source_may_be_development_only(self):
        source = KnowledgeSource.model_validate(
            make_source(content_scope="development_only")
        )
        assert source.content_scope == "development_only"

    def test_ingested_requires_permission_and_approval(self):
        with pytest.raises(ValidationError, match="ingested"):
            KnowledgeSource.model_validate(make_source(ingestion_status="ingested"))


class TestSourceRegistry:
    def test_valid_registry(self):
        registry = SourceRegistry.model_validate(
            make_registry(make_source(id="a"), make_source(id="b"))
        )
        assert [s.id for s in registry.sources] == ["a", "b"]

    def test_rejects_duplicate_ids(self):
        with pytest.raises(ValidationError, match="Duplicate source IDs: dup"):
            SourceRegistry.model_validate(
                make_registry(make_source(id="dup"), make_source(id="dup"))
            )

    def test_rejects_topic_mismatch(self):
        with pytest.raises(ValidationError, match="do not match registry topic"):
            SourceRegistry.model_validate(
                make_registry(make_source(topic="ovarian-cysts"))
            )

    def test_rejects_unexpected_registry_field(self):
        with pytest.raises(ValidationError):
            SourceRegistry.model_validate({**make_registry(), "extra": True})


# ── Ingestion eligibility ─────────────────────────────────────────


class TestIngestionEligibility:
    def test_eligible_when_all_conditions_met(self):
        assert is_eligible_for_ingestion(
            KnowledgeSource.model_validate(make_source(**ELIGIBLE))
        )

    def test_unknown_permission_is_not_eligible(self):
        source = KnowledgeSource.model_validate(
            make_source(**{**ELIGIBLE, "ingestion_permission": "not_verified"})
        )
        assert not is_eligible_for_ingestion(source)

    @pytest.mark.parametrize(
        "overrides",
        [
            {"ingestion_permission": "prohibited"},
            {"clinical_review_status": "not_reviewed"},
            {"clinical_review_status": "in_review"},
            {"clinical_review_status": "rejected"},
        ],
    )
    def test_not_eligible_when_any_condition_fails(self, overrides):
        source = KnowledgeSource.model_validate(
            make_source(**{**ELIGIBLE, **overrides})
        )
        assert not is_eligible_for_ingestion(source)

    def test_clinical_approval_alone_is_not_eligible(self):
        source = KnowledgeSource.model_validate(
            make_source(clinical_review_status=ClinicalReviewStatus.APPROVED)
        )
        assert not is_eligible_for_ingestion(source)

    @pytest.mark.parametrize(
        "field", ["license", "authorization_reference", "authorization_date"]
    )
    def test_missing_evidence_is_not_eligible_even_if_validation_bypassed(self, field):
        source = KnowledgeSource.model_validate(make_source(**ELIGIBLE))
        unvalidated = source.model_copy(update={field: None})
        assert not is_eligible_for_ingestion(unvalidated)


# ── Committed PCOS registry ───────────────────────────────────────


class TestPcosRegistry:
    def test_loads_and_contains_expected_sources(self):
        registry = load_registry(SOURCES_DIR / "pcos.json")
        assert registry.topic == "pcos"
        assert {s.id for s in registry.sources} == {
            "who-pcos",
            "fda-pcos",
            "monash-pcos-guideline",
        }

    def test_fda_is_only_an_unreviewed_development_candidate(self):
        registry = load_registry(SOURCES_DIR / "pcos.json")
        candidate = next(s for s in registry.sources if s.id == "fda-pcos")
        assert candidate.content_scope == "development_only"
        assert candidate.clinical_review_status == "not_reviewed"
        assert candidate.ingestion_permission == "not_verified"
        assert not is_eligible_for_ingestion(candidate)

    def test_no_source_is_eligible_or_ingested(self):
        registry = load_registry(SOURCES_DIR / "pcos.json")
        assert not any(is_eligible_for_ingestion(s) for s in registry.sources)
        assert all(s.ingestion_status == "metadata_only" for s in registry.sources)


# ── Inspection script ─────────────────────────────────────────────


class TestInspectSources:
    def test_default_registry(self, capsys):
        assert inspect_main([]) == 0
        out = capsys.readouterr().out
        assert "who-pcos" in out
        assert "World Health Organization" in out
        assert "Total sources: 3" in out
        assert "Not approved for ingestion (3):" in out

    def test_reports_eligible_sources(self, tmp_path, capsys):
        path = write_registry(tmp_path, make_registry(make_source(**ELIGIBLE)))
        assert inspect_main([path]) == 0
        out = capsys.readouterr().out
        assert "Total sources: 1" in out
        assert "All sources are approved for ingestion." in out

    def test_invalid_registry_exits_with_error(self, tmp_path, capsys):
        path = write_registry(
            tmp_path, make_registry(make_source(id="dup"), make_source(id="dup"))
        )
        assert inspect_main([path]) == 1
        captured = capsys.readouterr()
        assert "ERROR: invalid registry" in captured.err
        assert "Duplicate source IDs" in captured.err
        assert captured.out == ""

    def test_malformed_json_exits_with_error(self, tmp_path, capsys):
        path = write_registry(tmp_path, "{not json")
        assert inspect_main([path]) == 1
        assert "ERROR: invalid registry" in capsys.readouterr().err

    def test_missing_file_exits_with_error(self, tmp_path, capsys):
        assert inspect_main([str(tmp_path / "missing.json")]) == 1
        assert "ERROR: cannot read registry" in capsys.readouterr().err
