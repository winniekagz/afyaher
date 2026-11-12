"""Offline tests: fictional passages, fake credentials and mocked provider calls."""

import io
import json
import logging
from types import SimpleNamespace
from urllib.error import URLError
from urllib.request import Request

import pytest

from app.schemas.knowledge import KnowledgeSource, RetrievedPassage, SourceRegistry
from app.services import research_retrieval as research
from app.services.knowledge import SYNTHETIC_DIR, load_registry
from app.services.retrieval import load_passage_sets
from scripts.search_passages_with_llm import main as search_main
from tests.test_knowledge import ELIGIBLE, make_source

MODEL = "example/fixture-model:free"
KEY = "synthetic-test-key"


@pytest.fixture
def corpus():
    registry = load_registry(SYNTHETIC_DIR / "registry.json")
    stored = load_passage_sets(SYNTHETIC_DIR / "passages")[0].passages[:2]
    records = [
        RetrievedPassage(passage=p, score=1, matched_terms=["fictional"])
        for p in stored
    ]
    return registry, records


def completion(ids: object) -> dict:
    return {
        "model": MODEL,
        "usage": {"cost": 0},
        "choices": [{"message": {"content": json.dumps({"passage_ids": ids})}}],
    }


@pytest.fixture
def transport(monkeypatch):
    calls: list[Request] = []
    replies = {
        "catalogue": {
            "data": [{"id": MODEL, "pricing": {"prompt": "0", "completion": "0"}}]
        },
        "completion": completion([]),
    }

    def request(request: Request, max_bytes: int) -> object:
        calls.append(request)
        return (
            replies["catalogue"]
            if request.get_method() == "GET"
            else replies["completion"]
        )

    monkeypatch.setattr(research, "_request_json", request)
    return calls, replies


def select(corpus, **overrides):
    registry, records = corpus
    options = {"api_key": KEY, "model": MODEL, "provider": "reviewed-test-provider"}
    return research.select_synthetic_passages(
        "fictional lanterns", records, registry, **(options | overrides)
    )


def test_selects_only_original_retrieved_text_and_enforces_free_routing(
    corpus, transport
):
    calls, replies = transport
    passages = [r.passage for r in corpus[1]]
    replies["completion"] = completion([p.id for p in reversed(passages)])
    assert select(corpus) == list(reversed(passages))
    assert len(calls) == 2
    assert calls[0].get_header("Authorization") is None
    assert calls[1].get_header("Authorization") == f"Bearer {KEY}"
    payload = json.loads(calls[1].data)
    assert payload["model"] == MODEL
    assert "models" not in payload  # No paid model fallback array.
    assert "tools" not in payload and "plugins" not in payload
    assert payload["provider"] == {
        "only": ["reviewed-test-provider"],
        "allow_fallbacks": False,
        "require_parameters": True,
        "data_collection": "deny",
        "zdr": True,
        "max_price": {"prompt": 0, "completion": 0, "request": 0},
    }
    assert KEY not in calls[1].data.decode()


def test_empty_retrieval_never_contacts_a_provider(corpus, transport):
    assert select((corpus[0], [])) == []
    assert transport[0] == []


@pytest.mark.parametrize("missing", ["api_key", "provider"])
def test_missing_configuration_makes_no_request(corpus, transport, missing):
    with pytest.raises(research.ResearchRetrievalError, match="Configure"):
        select(corpus, **{missing: ""})
    assert transport[0] == []


@pytest.mark.parametrize("model", ["openrouter/free", "example/paid-model", ""])
def test_refuses_random_router_and_nonfree_models(corpus, transport, model):
    with pytest.raises(research.ResearchRetrievalError, match="explicitly free"):
        select(corpus, model=model)
    assert all(call.get_method() == "GET" for call in transport[0])


@pytest.mark.parametrize(
    "item",
    [
        {"id": MODEL, "pricing": {"prompt": "0", "completion": "1"}},
        {"id": MODEL, "pricing": {"prompt": "0", "completion": "0", "request": "1"}},
        {"id": MODEL, "pricing": {"prompt": "0"}},
        {"id": MODEL, "pricing": {"prompt": "unknown", "completion": "0"}},
        {"id": "example/paid", "pricing": {"prompt": "0", "completion": "0"}},
        None,
    ],
)
def test_catalogue_excludes_unverified_or_nonzero_prices(transport, item):
    transport[1]["catalogue"] = {"data": [item]}
    assert research.list_free_models() == []


def test_rejects_malformed_catalogue(transport):
    transport[1]["catalogue"] = {"data": "untrusted"}
    with pytest.raises(research.ResearchRetrievalError, match="catalogue"):
        research.list_free_models()


@pytest.mark.parametrize("ids", [["invented-p0"], [42], "not-a-list", None])
def test_model_cannot_invent_passages(corpus, transport, ids):
    transport[1]["completion"] = completion(ids)
    with pytest.raises(research.ResearchRetrievalError, match="failed validation"):
        select(corpus)


def test_duplicate_selected_ids_reject_the_result(corpus, transport):
    passage_id = corpus[1][0].passage.id
    transport[1]["completion"] = completion([passage_id, passage_id])
    with pytest.raises(research.ResearchRetrievalError, match="failed validation"):
        select(corpus)


@pytest.mark.parametrize(
    "overrides",
    [
        {"model": "example/unexpected-model"},
        {"usage": {"cost": 1}},
        {"usage": {}},
        {"choices": []},
        {"choices": [{"message": {"content": "not JSON"}}]},
        {
            "choices": [
                {"message": {"content": '{"passage_ids": [], "claim": "fiction"}'}}
            ]
        },
    ],
)
def test_rejects_unverified_cost_model_or_output(corpus, transport, overrides):
    transport[1]["completion"] = completion([]) | overrides
    with pytest.raises(research.ResearchRetrievalError, match="failed validation"):
        select(corpus)


def test_real_sources_are_rejected_even_with_fictional_approval(corpus, transport):
    registry, records = corpus
    real = KnowledgeSource.model_validate(
        make_source(id=records[0].passage.source_id, **ELIGIBLE)
    )
    real_registry = SourceRegistry(topic="pcos", sources=[real])
    with pytest.raises(research.ResearchRetrievalError, match="synthetic fixtures"):
        select((real_registry, records))
    assert transport[0] == []


def test_mixed_batch_never_sends_partial_context(corpus, transport):
    registry, records = corpus
    orphan = records[0].model_copy(deep=True)
    orphan.passage.source_id = "unknown"
    with pytest.raises(research.ResearchRetrievalError, match="synthetic fixtures"):
        select((registry, [records[0], orphan]))
    assert transport[0] == []


def test_rejects_duplicate_candidate_ids(corpus, transport):
    with pytest.raises(research.ResearchRetrievalError, match="synthetic fixtures"):
        select((corpus[0], [corpus[1][0], corpus[1][0]]))
    assert transport[0] == []


def test_revalidates_passage_positions(corpus, transport):
    corpus[1][0].passage.position = -1
    with pytest.raises(
        research.ResearchRetrievalError, match="Invalid research passage"
    ):
        select(corpus)
    assert transport[0] == []


def test_selection_does_not_log_content_or_credentials(
    corpus, transport, caplog, capsys
):
    with caplog.at_level(logging.DEBUG):
        assert select(corpus) == []
    assert not caplog.records
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


@pytest.mark.parametrize("raw", [b"not-json", b"x" * 11])
def test_transport_rejects_invalid_or_oversized_responses(monkeypatch, raw):
    def open_response(request, timeout):
        assert timeout == 15
        return io.BytesIO(raw)

    monkeypatch.setattr(
        research, "build_opener", lambda *args: SimpleNamespace(open=open_response)
    )
    with pytest.raises(research.ResearchRetrievalError):
        research._request_json(Request(f"{research.API_ROOT}/models"), 10)


def test_transport_masks_error_details(monkeypatch):
    def fail(*args, **kwargs):
        raise URLError(f"private detail {KEY}")

    monkeypatch.setattr(
        research, "build_opener", lambda *args: SimpleNamespace(open=fail)
    )
    with pytest.raises(research.ResearchRetrievalError) as result:
        research._request_json(Request(f"{research.API_ROOT}/models"), 100)
    assert KEY not in str(result.value)


def test_transport_refuses_redirects():
    with pytest.raises(research.ResearchRetrievalError, match="redirects"):
        research._NoRedirects().redirect_request(
            None, None, 302, "", None, "https://fixtures.invalid"
        )


def test_cli_preview_does_not_contact_provider(transport, capsys):
    assert search_main(["green lanterns"]) == 0
    output = capsys.readouterr().out
    assert "no LLM call" in output
    assert "synthetic-lantern-archive-p" in output
    assert "green lanterns" not in output
    assert not transport[0]


def test_cli_requires_explicit_consent_for_live_data(transport, capsys):
    assert search_main(["fictional query", "--live"]) == 1
    assert "confirm" in capsys.readouterr().err
    assert not transport[0]


def test_cli_live_failure_does_not_echo_secret_or_query(monkeypatch, transport, capsys):
    monkeypatch.setenv("AFYAHER_RESEARCH_API_KEY", KEY)
    monkeypatch.setenv("AFYAHER_RESEARCH_MODEL", "example/paid-model")
    monkeypatch.setenv("AFYAHER_RESEARCH_PROVIDER", "test-provider")
    assert search_main(["fictional query", "--live", "--confirm-synthetic-data"]) == 1
    output = capsys.readouterr().err
    assert KEY not in output and "fictional query" not in output


def test_cli_live_accepts_an_empty_selection(monkeypatch, transport, capsys):
    monkeypatch.setenv("AFYAHER_RESEARCH_API_KEY", KEY)
    monkeypatch.setenv("AFYAHER_RESEARCH_MODEL", MODEL)
    monkeypatch.setenv("AFYAHER_RESEARCH_PROVIDER", "test-provider")
    assert (
        search_main(["fictional lanterns", "--live", "--confirm-synthetic-data"]) == 0
    )
    assert "Selected 0 passage(s)" in capsys.readouterr().out
