"""Tests for SourcePassage, chunking, and citation mapping.

All text is synthetic placeholder prose with no medical claims.
"""

import json
import random

import pytest
from pydantic import ValidationError

from app.schemas.knowledge import (
    MAX_PASSAGE_CHARS,
    ContentScope,
    KnowledgeSource,
    PassageSet,
    SourcePassage,
    SourceRegistry,
)
from app.services.chunking import (
    EmptyContentError,
    IneligibleSourceError,
    chunk_text,
)
from app.services.citations import CitationError, resolve_citations
from app.services.knowledge import (
    SOURCES_DIR,
    SYNTHETIC_DIR,
    can_chunk,
    is_eligible_for_ingestion,
    is_eligible_for_production_retrieval,
    load_registry,
)
from scripts.build_passages import main as build_main
from tests.test_knowledge import ELIGIBLE, make_source

SYNTHETIC_TEXT = (
    "Alpha paragraph one. It has two sentences.\n\n"
    "Bravo paragraph two is here.\n\n"
    "Charlie paragraph three closes the sample."
)


def eligible_source(source_id: str = "synthetic-source") -> KnowledgeSource:
    return KnowledgeSource.model_validate(make_source(id=source_id, **ELIGIBLE))


def visible_chars(text: str) -> str:
    return "".join(text.split())


def assert_valid_chunking(text: str, passages: list[SourcePassage], max_chars: int):
    """Check the documented chunking invariants for one input."""
    assert passages, "non-empty input must produce passages"
    assert visible_chars("".join(p.text for p in passages)) == visible_chars(text)
    assert all(p.text and p.text == p.text.strip() for p in passages)
    assert all(len(p.text) <= max_chars for p in passages)
    assert [p.position for p in passages] == list(range(len(passages)))
    assert [p.id for p in passages] == [
        f"{p.source_id}-p{p.position}" for p in passages
    ]


def make_passage(**overrides) -> dict:
    passage = {
        "id": "synthetic-source-p0",
        "source_id": "synthetic-source",
        "topic": "pcos",
        "position": 0,
        "text": "Synthetic placeholder passage.",
    }
    passage.update(overrides)
    return passage


# ── SourcePassage schema ──────────────────────────────────────────


class TestSourcePassage:
    def test_valid_passage(self):
        passage = SourcePassage.model_validate(make_passage(text="  padded  "))
        assert passage.text == "padded"

    @pytest.mark.parametrize("text", ["", "   ", "x" * (MAX_PASSAGE_CHARS + 1)])
    def test_rejects_invalid_text(self, text):
        with pytest.raises(ValidationError, match="text"):
            SourcePassage.model_validate(make_passage(text=text))

    def test_rejects_negative_position(self):
        with pytest.raises(ValidationError, match="position"):
            SourcePassage.model_validate(make_passage(position=-1))

    @pytest.mark.parametrize("field", ["id", "source_id"])
    def test_rejects_non_slug_ids(self, field):
        with pytest.raises(ValidationError, match=field):
            SourcePassage.model_validate(make_passage(**{field: "Not A Slug"}))

    def test_rejects_unsupported_topic(self):
        with pytest.raises(ValidationError, match="topic"):
            SourcePassage.model_validate(make_passage(topic="endometriosis"))

    def test_rejects_unexpected_field(self):
        with pytest.raises(ValidationError, match="embedding"):
            SourcePassage.model_validate(make_passage(embedding=[0.1]))


# ── Chunking ──────────────────────────────────────────────────────


class TestChunking:
    def test_refuses_ineligible_source(self):
        source = KnowledgeSource.model_validate(make_source())
        with pytest.raises(IneligibleSourceError, match="not eligible"):
            chunk_text(source, SYNTHETIC_TEXT)

    def test_committed_pcos_sources_cannot_be_chunked(self):
        for source in load_registry(SOURCES_DIR / "pcos.json").sources:
            with pytest.raises(IneligibleSourceError):
                chunk_text(source, SYNTHETIC_TEXT)

    def test_packs_paragraphs_that_fit(self):
        passages = chunk_text(eligible_source(), SYNTHETIC_TEXT)
        assert len(passages) == 1
        assert passages[0].text.count("\n\n") == 2

    def test_splits_paragraphs_when_limit_reached(self):
        passages = chunk_text(eligible_source(), SYNTHETIC_TEXT, max_chars=45)
        assert [p.text for p in passages] == [
            "Alpha paragraph one. It has two sentences.",
            "Bravo paragraph two is here.",
            "Charlie paragraph three closes the sample.",
        ]

    def test_splits_long_paragraph_on_sentences(self):
        text = "First sentence here. Second sentence here. Third sentence here."
        passages = chunk_text(eligible_source(), text, max_chars=45)
        assert [p.text for p in passages] == [
            "First sentence here. Second sentence here.",
            "Third sentence here.",
        ]

    def test_splits_long_sentence_on_whitespace(self):
        text = " ".join(["word"] * 30)
        passages = chunk_text(eligible_source(), text, max_chars=20)
        assert all(len(p.text) <= 20 for p in passages)
        assert " ".join(p.text for p in passages) == text

    def test_hard_splits_unbroken_text(self):
        passages = chunk_text(eligible_source(), "x" * 25, max_chars=10)
        assert [len(p.text) for p in passages] == [10, 10, 5]

    def test_preserves_all_words_in_order(self):
        passages = chunk_text(eligible_source(), SYNTHETIC_TEXT, max_chars=30)
        rejoined = " ".join(p.text for p in passages).split()
        assert rejoined == SYNTHETIC_TEXT.split()
        assert all(len(p.text) <= 30 for p in passages)

    def test_passages_link_to_source_with_stable_ids(self):
        passages = chunk_text(eligible_source("demo"), SYNTHETIC_TEXT, max_chars=45)
        assert [p.id for p in passages] == ["demo-p0", "demo-p1", "demo-p2"]
        assert [p.position for p in passages] == [0, 1, 2]
        assert {p.source_id for p in passages} == {"demo"}
        assert {p.topic for p in passages} == {"pcos"}

    @pytest.mark.parametrize(
        "text",
        ["", "   \n\n  ", "\t\r\n", "\u00a0\u3000\u2003\u2028", "\n\u3000\n"],
        ids=["empty", "spaces", "control", "unicode-spaces", "ideographic-lines"],
    )
    def test_rejects_blank_text(self, text):
        with pytest.raises(EmptyContentError, match="synthetic-source"):
            chunk_text(eligible_source(), text)

    def test_ineligibility_takes_precedence_over_other_errors(self):
        source = KnowledgeSource.model_validate(make_source())
        with pytest.raises(IneligibleSourceError):
            chunk_text(source, "", max_chars=0)

    def test_invalid_max_chars_takes_precedence_over_empty_text(self):
        with pytest.raises(ValueError, match="max_chars") as exc_info:
            chunk_text(eligible_source(), "", max_chars=0)
        assert not isinstance(exc_info.value, EmptyContentError)

    def test_single_short_document(self):
        passages = chunk_text(eligible_source(), "  One short line.  ")
        assert [p.text for p in passages] == ["One short line."]
        assert_valid_chunking("One short line.", passages, 1200)

    @pytest.mark.parametrize(
        ("text", "max_chars", "expected"),
        [
            ("Hello. World.", 6, ["Hello.", "World."]),
            ("日本語の文です。次の文です。", 8, ["日本語の文です。", "次の文です。"]),
            ("Ndiyo。 日本語の文です。", 8, ["Ndiyo。", "日本語の文です。"]),
            ("Ça va… Très bien!", 10, ["Ça va…", "Très bien!"]),
            ("Kweli！？ Ndiyo？", 7, ["Kweli！？", "Ndiyo？"]),
        ],
        ids=["english", "japanese-no-space", "mixed-space", "ellipsis", "fullwidth"],
    )
    def test_multilingual_sentence_boundaries(self, text, max_chars, expected):
        passages = chunk_text(eligible_source(), text, max_chars=max_chars)
        assert [p.text for p in passages] == expected

    def test_does_not_split_inside_decimal_numbers(self):
        passages = chunk_text(eligible_source(), "Version 3.5 here. Next.", 18)
        assert passages[0].text == "Version 3.5 here."

    def test_japanese_sentences_rejoin_without_inserted_spaces(self):
        text = "一つ目。二つ目。三つ目。"
        passages = chunk_text(eligible_source(), text, max_chars=8)
        assert [p.text for p in passages] == ["一つ目。二つ目。", "三つ目。"]

    def test_mixed_language_document(self):
        text = (
            "Habari ya asubuhi. Hii ni sentensi ya majaribio.\n\n"
            "Ça va… Très bien! Voilà une phrase d’essai.\n\n"
            "これは試験の文です。次の文もあります。最後の文。"
        )
        for max_chars in (12, 25, 60, 1200):
            passages = chunk_text(eligible_source(), text, max_chars=max_chars)
            assert_valid_chunking(text, passages, max_chars)

    def test_multiple_paragraphs_preserved(self):
        passages = chunk_text(eligible_source(), SYNTHETIC_TEXT, max_chars=60)
        assert_valid_chunking(SYNTHETIC_TEXT, passages, 60)

    def test_long_paragraph_preserved(self):
        text = " ".join(f"Sentence number {i} is synthetic." for i in range(200))
        passages = chunk_text(eligible_source(), text, max_chars=300)
        assert len(passages) > 1
        assert_valid_chunking(text, passages, 300)

    def test_text_exactly_max_chars_is_one_passage(self):
        passages = chunk_text(eligible_source(), "abcde fghij", max_chars=11)
        assert [p.text for p in passages] == ["abcde fghij"]

    def test_one_char_over_max_chars_splits_without_loss(self):
        passages = chunk_text(eligible_source(), "abcde fghijk", max_chars=11)
        assert [p.text for p in passages] == ["abcde", "fghijk"]

    def test_space_exactly_at_boundary(self):
        passages = chunk_text(eligible_source(), "abcdefghij klm", max_chars=10)
        assert [p.text for p in passages] == ["abcdefghij", "klm"]

    def test_paragraphs_exactly_filling_max_chars_are_packed(self):
        text = "abcd\n\nefgh"
        passages = chunk_text(eligible_source(), text, max_chars=10)
        assert [p.text for p in passages] == ["abcd\n\nefgh"]

    def test_max_chars_of_one(self):
        passages = chunk_text(eligible_source(), "ab c。d", max_chars=1)
        assert [p.text for p in passages] == ["a", "b", "c", "。", "d"]

    def test_chunking_is_deterministic(self):
        text = SYNTHETIC_TEXT * 5
        first = chunk_text(eligible_source(), text, max_chars=50)
        second = chunk_text(eligible_source(), text, max_chars=50)
        assert first == second

    @pytest.mark.parametrize("seed", range(25))
    def test_randomised_inputs_satisfy_invariants(self, seed):
        rng = random.Random(seed)
        alphabet = list("abcxyz日本ñé") + [" ", "  ", "\n", "\n\n", "\t"]
        alphabet += [". ", "! ", "? ", "… ", "。", "！", "？", "\u3000", "\u00a0"]
        text = "z" + "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 400)))
        max_chars = rng.randint(1, 80)
        passages = chunk_text(eligible_source(), text, max_chars=max_chars)
        assert_valid_chunking(text, passages, max_chars)

    @pytest.mark.parametrize(
        "max_chars", [0, -1, MAX_PASSAGE_CHARS + 1, True, False, 2.5, "10", None]
    )
    def test_rejects_invalid_max_chars(self, max_chars):
        with pytest.raises(ValueError, match="max_chars"):
            chunk_text(eligible_source(), SYNTHETIC_TEXT, max_chars=max_chars)

    @pytest.mark.parametrize("punctuation", [".", "!", "?", "。", "！", "？", "…"])
    def test_each_sentence_separator_preserves_content(self, punctuation):
        text = f"Alpha{punctuation} Beta{punctuation} Gamma{punctuation}"
        passages = chunk_text(eligible_source(), text, max_chars=10)
        assert [p.text for p in passages] == [
            f"Alpha{punctuation}",
            f"Beta{punctuation}",
            f"Gamma{punctuation}",
        ]
        assert_valid_chunking(text, passages, 10)

    @pytest.mark.parametrize("max_chars", [1, 2, 5, 12, 30])
    def test_adjacent_punctuation_runs_preserve_content(self, max_chars):
        text = "！？次。Really?! Oui…！？終わり。"
        passages = chunk_text(eligible_source(), text, max_chars=max_chars)
        assert_valid_chunking(text, passages, max_chars)


# ── Citation mapping ──────────────────────────────────────────────


def registry_with(*sources: KnowledgeSource) -> SourceRegistry:
    return SourceRegistry(topic="pcos", sources=list(sources))


class TestCitations:
    def setup_method(self):
        self.source_a = eligible_source("source-a")
        self.source_b = eligible_source("source-b")
        self.registry = registry_with(self.source_a, self.source_b)
        self.retrieved = [
            SourcePassage.model_validate(
                make_passage(id="source-a-p0", source_id="source-a")
            ),
            SourcePassage.model_validate(
                make_passage(id="source-a-p1", source_id="source-a", position=1)
            ),
            SourcePassage.model_validate(
                make_passage(id="source-b-p0", source_id="source-b")
            ),
        ]

    def test_maps_citations_to_registry_metadata(self):
        refs = resolve_citations(["source-b-p0"], self.retrieved, self.registry)
        assert len(refs) == 1
        assert refs[0].id == "source-b"
        assert refs[0].title == self.source_b.title
        assert refs[0].url == self.source_b.url

    def test_deduplicates_sources_in_first_cited_order(self):
        refs = resolve_citations(
            ["source-b-p0", "source-a-p1", "source-a-p0"],
            self.retrieved,
            self.registry,
        )
        assert [r.id for r in refs] == ["source-b", "source-a"]

    def test_no_citations_returns_empty_list(self):
        assert resolve_citations([], self.retrieved, self.registry) == []

    def test_rejects_citation_not_retrieved(self):
        with pytest.raises(CitationError, match="invented-p9"):
            resolve_citations(["invented-p9"], self.retrieved, self.registry)

    def test_rejects_passage_from_unknown_source(self):
        orphan = SourcePassage.model_validate(
            make_passage(id="ghost-p0", source_id="ghost")
        )
        with pytest.raises(CitationError, match="unknown source 'ghost'"):
            resolve_citations(["ghost-p0"], [orphan], self.registry)

    def test_rejects_passage_from_ineligible_source(self):
        registry = registry_with(
            KnowledgeSource.model_validate(make_source(id="source-a"))
        )
        with pytest.raises(CitationError, match="ineligible source 'source-a'"):
            resolve_citations(["source-a-p0"], self.retrieved, registry)

    def test_rejects_duplicate_retrieved_ids(self):
        ambiguous = self.retrieved + [self.retrieved[0]]
        with pytest.raises(CitationError, match="Duplicate retrieved passage ID"):
            resolve_citations(["source-a-p0"], ambiguous, self.registry)

    @pytest.mark.parametrize(
        "overrides",
        [{"topic": "ovarian-cysts"}, {"id": "source-b-p0"}, {"position": 9}],
    )
    def test_rejects_inconsistent_source_metadata(self, overrides):
        passage = SourcePassage.model_validate(
            make_passage(id="source-a-p0", source_id="source-a") | overrides
        )
        with pytest.raises(CitationError, match="inconsistent source metadata"):
            resolve_citations([passage.id], [passage], self.registry)


# ── Synthetic versus production policies ──────────────────────────


def synthetic_source(**overrides) -> KnowledgeSource:
    fields = {
        "id": "synthetic-demo",
        "evidence_type": "synthetic_fixture",
        "content_scope": "development_only",
        **overrides,
    }
    return KnowledgeSource.model_validate(make_source(**fields))


class TestContentPolicies:
    def test_legacy_eligible_source_requires_explicit_production_scope(self):
        data = make_source(**ELIGIBLE)
        del data["content_scope"]
        source = KnowledgeSource.model_validate(data)
        assert can_chunk(source)
        assert not is_eligible_for_production_retrieval(source)

    def test_eligible_production_source_passes_every_policy(self):
        source = eligible_source()
        assert is_eligible_for_ingestion(source)
        assert can_chunk(source)
        assert is_eligible_for_production_retrieval(source)

    def test_eligible_source_scoped_development_is_not_production(self):
        source = KnowledgeSource.model_validate(
            make_source(**ELIGIBLE, content_scope="development_only")
        )
        assert can_chunk(source)
        assert not is_eligible_for_production_retrieval(source)

    def test_ineligible_real_source_fails_every_policy(self):
        source = KnowledgeSource.model_validate(make_source())
        assert not can_chunk(source)
        assert not is_eligible_for_production_retrieval(source)

    def test_synthetic_fixture_can_be_chunked(self):
        source = synthetic_source()
        assert can_chunk(source)
        assert not is_eligible_for_ingestion(source)
        assert not is_eligible_for_production_retrieval(source)

    def test_fully_approved_synthetic_fixture_is_never_production_eligible(self):
        source = synthetic_source(**ELIGIBLE)
        assert is_eligible_for_ingestion(source)
        assert not is_eligible_for_production_retrieval(source)

    def test_bypassed_validation_cannot_make_synthetic_production_eligible(self):
        source = synthetic_source(**ELIGIBLE).model_copy(
            update={"content_scope": ContentScope.PRODUCTION}
        )
        assert not can_chunk(source)
        assert not is_eligible_for_production_retrieval(source)

    def test_committed_pcos_sources_are_unchanged(self):
        for source in load_registry(SOURCES_DIR / "pcos.json").sources:
            assert source.content_scope == "production"
            assert source.evidence_type != "synthetic_fixture"
            assert not can_chunk(source)
            assert not is_eligible_for_production_retrieval(source)


class TestSyntheticCitations:
    def test_production_citations_reject_synthetic_passages(self):
        source = synthetic_source()
        passages = chunk_text(source, "Invented sentence. Another one.")
        registry = registry_with(source)
        with pytest.raises(CitationError, match="not eligible for production"):
            resolve_citations([passages[0].id], passages, registry)

    def test_rejects_approved_synthetic_passages(self):
        source = synthetic_source(**ELIGIBLE)
        passages = chunk_text(source, "Invented sentence.")
        with pytest.raises(CitationError, match="synthetic-demo"):
            resolve_citations([passages[0].id], passages, registry_with(source))

    def test_rejects_development_scoped_real_source(self):
        source = KnowledgeSource.model_validate(
            make_source(**ELIGIBLE, content_scope="development_only")
        )
        passages = chunk_text(source, "Placeholder.")
        with pytest.raises(CitationError):
            resolve_citations([passages[0].id], passages, registry_with(source))

    def test_mixed_retrieval_still_rejects_synthetic_citation(self):
        real = eligible_source("real-source")
        fake = synthetic_source()
        retrieved = chunk_text(real, "Placeholder one.") + chunk_text(fake, "Two.")
        registry = registry_with(real, fake)
        refs = resolve_citations(["real-source-p0"], retrieved, registry)
        assert [r.id for r in refs] == ["real-source"]
        with pytest.raises(CitationError, match="synthetic-demo"):
            resolve_citations(
                ["real-source-p0", "synthetic-demo-p0"], retrieved, registry
            )


# ── Committed synthetic fixture ───────────────────────────────────


FIXTURE_REGISTRY = SYNTHETIC_DIR / "registry.json"
FIXTURE_ID = "synthetic-lantern-archive"


class TestSyntheticFixture:
    def setup_method(self):
        self.registry = load_registry(FIXTURE_REGISTRY)
        self.source = self.registry.sources[0]
        self.text = (SYNTHETIC_DIR / f"{FIXTURE_ID}.txt").read_text(encoding="utf-8")

    def test_fixture_is_unmistakably_synthetic(self):
        assert [s.id for s in self.registry.sources] == [FIXTURE_ID]
        assert self.source.evidence_type == "synthetic_fixture"
        assert self.source.content_scope == "development_only"
        assert self.source.clinical_review_status == "not_reviewed"
        assert self.source.ingestion_permission == "not_verified"
        assert "SYNTHETIC" in self.source.title
        assert self.source.url.host.endswith(".invalid")
        assert self.text.startswith("SYNTHETIC FIXTURE.")

    def test_fixture_is_stored_apart_from_medical_sources(self):
        medical_ids = {s.id for s in load_registry(SOURCES_DIR / "pcos.json").sources}
        assert FIXTURE_ID not in medical_ids
        assert SYNTHETIC_DIR.resolve() != SOURCES_DIR.resolve()

    def test_fixture_chunks_but_is_not_production_eligible(self):
        assert can_chunk(self.source)
        assert not is_eligible_for_production_retrieval(self.source)
        passages = chunk_text(self.source, self.text, max_chars=400)
        assert_valid_chunking(self.text, passages, 400)
        with pytest.raises(CitationError):
            resolve_citations([passages[0].id], passages, self.registry)

    def test_committed_passages_match_a_fresh_build(self):
        stored = PassageSet.model_validate_json(
            (SYNTHETIC_DIR / "passages" / f"{FIXTURE_ID}.json").read_text("utf-8")
        )
        rebuilt = chunk_text(self.source, self.text, max_chars=stored.max_chars)
        assert stored.passages == rebuilt
        assert stored.content_scope == "development_only"
        known = {s.id for s in self.registry.sources}
        assert all(p.source_id in known for p in stored.passages)


# ── PassageSet schema ─────────────────────────────────────────────


def make_passage_set(**overrides) -> dict:
    data = {
        "source_id": "synthetic-source",
        "content_scope": "development_only",
        "max_chars": 100,
        "passages": [
            make_passage(),
            make_passage(id="synthetic-source-p1", position=1),
        ],
    }
    data.update(overrides)
    return data


class TestPassageSet:
    def test_valid_passage_set(self):
        assert len(PassageSet.model_validate(make_passage_set()).passages) == 2

    def test_rejects_empty_passages(self):
        with pytest.raises(ValidationError, match="passages"):
            PassageSet.model_validate(make_passage_set(passages=[]))

    def test_rejects_text_exceeding_recorded_limit(self):
        with pytest.raises(ValidationError, match="exceeds passage set max_chars"):
            PassageSet.model_validate(make_passage_set(max_chars=5))

    def test_rejects_foreign_source_reference(self):
        passages = [make_passage(id="other-p0", source_id="other")]
        with pytest.raises(ValidationError, match="other sources: other"):
            PassageSet.model_validate(make_passage_set(passages=passages))

    def test_rejects_non_sequential_positions(self):
        passages = [make_passage(), make_passage(id="synthetic-source-p2", position=2)]
        with pytest.raises(ValidationError, match="sequential"):
            PassageSet.model_validate(make_passage_set(passages=passages))

    def test_rejects_non_deterministic_ids(self):
        passages = [make_passage(id="synthetic-source-first")]
        with pytest.raises(ValidationError, match="Passage IDs"):
            PassageSet.model_validate(make_passage_set(passages=passages))


# ── build_passages script ─────────────────────────────────────────


def write_fixture(tmp_path, source: dict, text: str | None) -> str:
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"topic": "pcos", "sources": [source]}))
    if text is not None:
        (tmp_path / f"{source['id']}.txt").write_text(text, encoding="utf-8")
    return str(registry)


SYNTHETIC_FIELDS = {
    "id": "synthetic-demo",
    "evidence_type": "synthetic_fixture",
    "content_scope": "development_only",
}


class TestBuildPassagesScript:
    def test_builds_synthetic_passages(self, tmp_path, capsys):
        registry = write_fixture(
            tmp_path, make_source(**SYNTHETIC_FIELDS), "One. Two.\n\nThree。四。"
        )
        out_dir = tmp_path / "out"
        assert build_main(["--registry", registry, "--out-dir", str(out_dir)]) == 0
        stored = PassageSet.model_validate_json(
            (out_dir / "synthetic-demo.json").read_text("utf-8")
        )
        assert stored.passages[0].id == "synthetic-demo-p0"
        out = capsys.readouterr().out
        assert "synthetic-demo-p0" in out
        assert "Built 1 passages from 1 source(s)." in out

    def test_default_build_matches_committed_output(self, tmp_path):
        assert build_main(["--out-dir", str(tmp_path)]) == 0
        built = (tmp_path / f"{FIXTURE_ID}.json").read_text("utf-8")
        committed = (SYNTHETIC_DIR / "passages" / f"{FIXTURE_ID}.json").read_text(
            "utf-8"
        )
        assert built == committed

    @pytest.mark.parametrize(
        "source",
        [make_source(id="real-source"), make_source(id="real-source", **ELIGIBLE)],
        ids=["unapproved-real", "approved-real"],
    )
    def test_refuses_real_sources(self, tmp_path, capsys, source):
        registry = write_fixture(tmp_path, source, "Placeholder text.")
        out_dir = tmp_path / "out"
        assert build_main(["--registry", registry, "--out-dir", str(out_dir)]) == 1
        assert "not a development-only synthetic fixture" in capsys.readouterr().err
        assert not out_dir.exists()

    @pytest.mark.parametrize("text", [None, "  \n "], ids=["missing", "blank"])
    def test_fails_on_missing_or_blank_text(self, tmp_path, capsys, text):
        registry = write_fixture(tmp_path, make_source(**SYNTHETIC_FIELDS), text)
        out_dir = tmp_path / "out"
        assert build_main(["--registry", registry, "--out-dir", str(out_dir)]) == 1
        assert "cannot build passages" in capsys.readouterr().err
        assert not out_dir.exists()

    def test_fails_on_invalid_registry(self, tmp_path, capsys):
        registry = tmp_path / "registry.json"
        registry.write_text("{}")
        assert build_main(["--registry", str(registry)]) == 1
        assert "invalid registry" in capsys.readouterr().err
