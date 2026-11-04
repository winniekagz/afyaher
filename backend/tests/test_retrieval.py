"""Tests for keyword retrieval and the retrieve -> cite pipeline.

All text is synthetic placeholder prose with no medical claims.
"""

import pytest
from pydantic import ValidationError

from app.schemas.educational import Topic
from app.schemas.knowledge import (
    ContentScope,
    KnowledgeSource,
    PassageSet,
    RetrievedPassage,
    SourceRegistry,
)
from app.services.chunking import chunk_text
from app.services.citations import CitationError, resolve_citations
from app.services.knowledge import SYNTHETIC_DIR, load_registry
from app.services.retrieval import (
    MAX_LIMIT,
    MAX_QUERY_CHARS,
    RetrievalError,
    load_passage_sets,
    retrieve,
    tokenize,
)
from scripts.search_passages import main as search_main
from tests.test_knowledge import ELIGIBLE, make_source

DEV = ContentScope.DEVELOPMENT_ONLY
PROD = ContentScope.PRODUCTION


def source(source_id: str, **fields) -> KnowledgeSource:
    return KnowledgeSource.model_validate(make_source(id=source_id, **fields))


def synthetic(source_id: str = "synthetic-demo") -> KnowledgeSource:
    return source(
        source_id, evidence_type="synthetic_fixture", content_scope="development_only"
    )


def passage_set(src: KnowledgeSource, text: str, max_chars: int = 60) -> PassageSet:
    return PassageSet(
        source_id=src.id,
        content_scope=src.content_scope,
        max_chars=max_chars,
        passages=chunk_text(src, text, max_chars=max_chars),
    )


REAL_TEXT = (
    "Copper kettles hum at noon.\n\n"
    "Silver kettles hum at dusk and copper bells ring.\n\n"
    "Wooden spoons rest quietly."
)
FAKE_TEXT = "Copper kettles appear in this invented fixture."


@pytest.fixture
def corpus():
    real = source("real-source", **ELIGIBLE)
    fake = synthetic()
    registry = SourceRegistry(topic="pcos", sources=[real, fake])
    sets = [passage_set(real, REAL_TEXT), passage_set(fake, FAKE_TEXT)]
    return registry, sets


def ids(results: list[RetrievedPassage]) -> list[str]:
    return [r.passage.id for r in results]


# ── Tokenisation ──────────────────────────────────────────────────


class TestTokenize:
    def test_casefolds_and_drops_stopwords(self):
        assert tokenize("What IS the Copper Kettle?") == ["copper", "kettle"]

    def test_normalises_unicode(self):
        assert tokenize("ＣＯＰＰＥＲ Straße") == ["copper", "strasse"]

    def test_keeps_accents_and_numbers(self):
        assert tokenize("Ça va 417") == ["ça", "va", "417"]

    def test_cjk_runs_become_bigrams(self):
        assert tokenize("灯りです") == ["灯り", "りで", "です"]

    def test_single_cjk_character(self):
        assert tokenize("灯") == ["灯"]

    @pytest.mark.parametrize("text", ["", "   ", "?!…", "the of is"])
    def test_no_terms(self, text):
        assert tokenize(text) == []


# ── Retrieval ─────────────────────────────────────────────────────


class TestRetrieve:
    def test_ranks_by_distinct_matched_terms(self, corpus):
        results = retrieve("copper bells", Topic.PCOS, *corpus)
        assert ids(results) == ["real-source-p1", "real-source-p0"]
        assert [r.score for r in results] == [2, 1]
        assert results[0].matched_terms == ["bells", "copper"]

    def test_ties_break_deterministically(self, corpus):
        first = retrieve("kettles hum", Topic.PCOS, *corpus)
        second = retrieve("hum kettles", Topic.PCOS, *corpus)
        assert ids(first) == ids(second) == ["real-source-p0", "real-source-p1"]

    def test_respects_limit(self, corpus):
        assert len(retrieve("kettles", Topic.PCOS, *corpus, limit=1)) == 1

    def test_no_match_returns_empty(self, corpus):
        assert retrieve("pancakes", Topic.PCOS, *corpus) == []

    def test_stopword_only_query_returns_empty(self, corpus):
        assert retrieve("what is the", Topic.PCOS, *corpus) == []

    def test_filters_by_topic(self, corpus):
        assert retrieve("copper", Topic.OVARIAN_CYSTS, *corpus) == []

    @pytest.mark.parametrize("query", ["", "   \n", "\u3000"])
    def test_rejects_empty_query(self, corpus, query):
        with pytest.raises(RetrievalError, match="empty"):
            retrieve(query, Topic.PCOS, *corpus)

    def test_rejects_oversized_query(self, corpus):
        with pytest.raises(RetrievalError, match="exceeds"):
            retrieve("a" * (MAX_QUERY_CHARS + 1), Topic.PCOS, *corpus)

    @pytest.mark.parametrize("limit", [0, MAX_LIMIT + 1])
    def test_rejects_invalid_limit(self, corpus, limit):
        with pytest.raises(RetrievalError, match="limit"):
            retrieve("copper", Topic.PCOS, *corpus, limit=limit)


class TestRetrievalScope:
    @pytest.mark.parametrize("scope", ["prodution", "staging", "", None])
    def test_unknown_scope_cannot_enable_development_retrieval(self, corpus, scope):
        with pytest.raises(RetrievalError, match="Unknown retrieval scope"):
            retrieve("invented fixture", Topic.PCOS, *corpus, scope=scope)

    def test_production_string_scope_excludes_synthetic(self, corpus):
        assert (
            retrieve("invented fixture", Topic.PCOS, *corpus, scope="production") == []
        )

    def test_production_scope_is_the_default_and_excludes_synthetic(self, corpus):
        results = retrieve("copper kettles", Topic.PCOS, *corpus, limit=10)
        assert results
        assert all(r.passage.source_id == "real-source" for r in results)

    def test_development_scope_includes_synthetic(self, corpus):
        results = retrieve("invented fixture", Topic.PCOS, *corpus, scope=DEV)
        assert ids(results) == ["synthetic-demo-p0"]

    def test_production_scope_excludes_development_scoped_real_source(self):
        dev_real = source("dev-real", **ELIGIBLE, content_scope="development_only")
        registry = SourceRegistry(topic="pcos", sources=[dev_real])
        sets = [passage_set(dev_real, "Copper kettles.")]
        assert retrieve("copper", Topic.PCOS, registry, sets, scope=PROD) == []
        assert retrieve("copper", Topic.PCOS, registry, sets, scope=DEV)

    def test_production_scope_on_synthetic_fixture_returns_nothing(self):
        registry = load_registry(SYNTHETIC_DIR / "registry.json")
        sets = load_passage_sets(SYNTHETIC_DIR / "passages")
        assert retrieve("green lanterns", Topic.PCOS, registry, sets) == []


class TestPassageConsistency:
    def test_rejects_passages_for_unknown_source(self, corpus):
        registry, sets = corpus
        orphan = passage_set(source("orphan", **ELIGIBLE), "Copper.")
        with pytest.raises(RetrievalError, match="unknown source 'orphan'"):
            retrieve("copper", Topic.PCOS, registry, [*sets, orphan])

    def test_rejects_duplicate_passage_sets(self, corpus):
        registry, sets = corpus
        with pytest.raises(RetrievalError, match="Duplicate"):
            retrieve("copper", Topic.PCOS, registry, [*sets, sets[0]])

    def test_rejects_passages_for_unchunkable_source(self):
        real = source("real-source", **ELIGIBLE)
        sets = [passage_set(real, "Copper.")]
        revoked = source("real-source")
        registry = SourceRegistry(topic="pcos", sources=[revoked])
        with pytest.raises(RetrievalError, match="unchunkable"):
            retrieve("copper", Topic.PCOS, registry, sets, scope=DEV)

    def test_rejects_scope_mismatch(self):
        real = source("real-source", **ELIGIBLE)
        stale = passage_set(real, "Copper.").model_copy(update={"content_scope": DEV})
        registry = SourceRegistry(topic="pcos", sources=[real])
        with pytest.raises(RetrievalError, match="scope"):
            retrieve("copper", Topic.PCOS, registry, [stale])

    def test_rejects_topic_mismatch(self):
        real = source("real-source", **ELIGIBLE)
        sets = [passage_set(real, "Copper.")]
        moved = source("real-source", **ELIGIBLE, topic="ovarian-cysts")
        registry = SourceRegistry(topic="ovarian-cysts", sources=[moved])
        with pytest.raises(RetrievalError, match="topic"):
            retrieve("copper", Topic.OVARIAN_CYSTS, registry, sets)


# ── Retrieve -> cite pipeline ─────────────────────────────────────


class TestRetrieveThenCite:
    def test_production_results_resolve_to_citations(self, corpus):
        registry, sets = corpus
        results = retrieve("copper bells", Topic.PCOS, registry, sets)
        retrieved = [r.passage for r in results]
        refs = resolve_citations([retrieved[0].id], retrieved, registry)
        assert [r.id for r in refs] == ["real-source"]

    def test_development_results_from_synthetic_cannot_be_cited(self, corpus):
        registry, sets = corpus
        results = retrieve("invented", Topic.PCOS, registry, sets, scope=DEV)
        retrieved = [r.passage for r in results]
        with pytest.raises(CitationError, match="synthetic-demo"):
            resolve_citations([retrieved[0].id], retrieved, registry)

    def test_citing_a_passage_that_was_not_retrieved_fails(self, corpus):
        registry, sets = corpus
        results = retrieve("copper bells", Topic.PCOS, registry, sets, limit=1)
        retrieved = [r.passage for r in results]
        with pytest.raises(CitationError, match="real-source-p2"):
            resolve_citations(["real-source-p2"], retrieved, registry)


class TestRetrievedPassageSchema:
    def test_rejects_zero_score(self, corpus):
        _, sets = corpus
        with pytest.raises(ValidationError, match="score"):
            RetrievedPassage(passage=sets[0].passages[0], score=0, matched_terms=["x"])

    def test_rejects_empty_matched_terms(self, corpus):
        _, sets = corpus
        with pytest.raises(ValidationError, match="matched_terms"):
            RetrievedPassage(passage=sets[0].passages[0], score=1, matched_terms=[])


# ── search_passages script ────────────────────────────────────────


class TestSearchScript:
    def test_finds_fixture_passage(self, capsys):
        assert search_main(["entry 417 violet"]) == 0
        out = capsys.readouterr().out
        assert "DEVELOPMENT ONLY" in out
        assert "synthetic-lantern-archive-p3" in out
        assert "1 passage(s) returned." in out

    def test_multilingual_query(self, capsys):
        assert search_main(["灯り"]) == 0
        assert "synthetic-lantern-archive-p4" in capsys.readouterr().out

    def test_reports_no_match(self, capsys):
        assert search_main(["pancakes"]) == 0
        assert "insufficient evidence" in capsys.readouterr().out

    def test_empty_query_fails(self, capsys):
        assert search_main(["   "]) == 1
        assert "Query is empty" in capsys.readouterr().err

    def test_missing_fixtures_fail(self, tmp_path, capsys):
        assert search_main(["x", "--fixtures", str(tmp_path)]) == 1
        assert "ERROR" in capsys.readouterr().err
