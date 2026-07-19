"""v1.2 router experiment: strategies, injection, split, matrix."""

import pytest
from typedmem import HashingEmbeddingProvider

from reliagent_bench.memory import load_tasks
from reliagent_bench.memory.dataset import build_store
from reliagent_bench.memory.router_experiment import (
    default_variants,
    router_failure_subtype,
    run_router_matrix,
    split_tasks,
)
from reliagent_bench.memory.router_pipeline import RouterPipelineRetriever
from reliagent_bench.memory.routers import (
    HybridRouter,
    LLMRouter,
    NoRouter,
    OracleRouter,
    RuleRouter,
    SoftRuleRouter,
)


class _StubClient:
    """Deterministic stand-in LLM: returns a fixed JSON routing per call."""

    def __init__(self, payload='{"types": ["goal"], "confidence": 0.9}'):
        self.payload = payload
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return self.payload


# ── strategies ──────────────────────────────────────────────────────────────
def test_rule_and_none_routers():
    assert RuleRouter().route("what coffee do I prefer?").types == ["preference"]
    assert NoRouter().route("anything").types == []


def test_soft_router_caps_top_n():
    r = SoftRuleRouter(top_n=1).route("what coffee do I prefer?")
    assert len(r.types) <= 1


def test_oracle_router_from_tasks():
    tasks = load_tasks()
    oracle = OracleRouter.from_tasks(tasks)
    g3 = next(t for t in tasks if t.id == "goal-03")
    assert oracle.route(g3.query).types == ["goal"]   # labeled expected type


def test_llm_router_cache_replay_and_miss():
    cache = {"v1::q": {"types": ["fact"], "confidence": 1.0}}
    # Cache hit → no client needed.
    assert LLMRouter(cache=cache).route("q").types == ["fact"]
    # Cache miss without a client → loud failure (reproducibility guard).
    with pytest.raises(RuntimeError):
        LLMRouter(cache={}).route("uncached")


def test_llm_router_with_client_caches():
    client = _StubClient()
    r = LLMRouter(client=client)
    out = r.route("some query")
    assert out.types == ["goal"] and out.used_llm is True
    assert r.calls == 1
    r.route("some query")            # second call served from cache
    assert client.calls == 1


def test_hybrid_uses_llm_only_when_rule_unconfident():
    client = _StubClient()
    hybrid = HybridRouter(RuleRouter(), LLMRouter(client=client))
    # Rule matches "prefer" → confident → LLM not called.
    hybrid.route("what do I prefer?")
    assert client.calls == 0
    # No rule match → LLM invoked.
    hybrid.route("xyzzy plugh")
    assert client.calls == 1


# ── injection + global fallback ──────────────────────────────────────────────
def test_global_fallback_recovers_over_filtered_memory():
    """goal-03 is over-filtered by the rule router (what is -> fact); the global
    fallback should recover the correct goal memory."""
    task = next(t for t in load_tasks() if t.id == "goal-03")
    store = build_store(task)
    emb = HashingEmbeddingProvider(dim=1024)

    hard = RouterPipelineRetriever(store, emb, RuleRouter(), global_fallback=False)
    assert hard.retrieve(task.query, 5) == []          # router empties the pool

    fb = RouterPipelineRetriever(store, emb, RuleRouter(), global_fallback=True)
    got = fb.retrieve(task.query, 5)
    assert "m2" in got                                 # current goal recovered
    assert fb.diagnostics["fallback_used"] is True


def test_diagnostics_recorded():
    task = next(t for t in load_tasks() if t.id == "temp-01")
    r = RouterPipelineRetriever(build_store(task), HashingEmbeddingProvider(dim=1024), NoRouter())
    r.retrieve(task.query, 5)
    d = r.diagnostics
    assert set(["predicted_types", "num_searched_types", "empty_result", "fallback_used"]) <= set(d)


def test_router_failure_subtype():
    task = next(t for t in load_tasks() if t.id == "goal-03")
    diag = {"predicted_types": ["fact"], "num_searched_types": 1,
            "empty_result": True, "fallback_used": False}
    # expected type is goal; predicted a single wrong type -> overly_narrow
    assert router_failure_subtype(task, diag) == "overly_narrow"


# ── split + matrix ────────────────────────────────────────────────────────────
def test_split_is_deterministic_and_stratified():
    tasks = load_tasks()
    dev, ev = split_tasks(tasks, eval_fraction=0.3, seed=0)
    assert len(dev) + len(ev) == len(tasks)
    assert {t.id for t in dev}.isdisjoint({t.id for t in ev})
    # every category represented in eval
    assert {t.category for t in ev} == {t.category for t in tasks}
    # deterministic
    dev2, ev2 = split_tasks(tasks, eval_fraction=0.3, seed=0)
    assert [t.id for t in ev] == [t.id for t in ev2]


def test_router_matrix_findings():
    tasks = load_tasks()
    results = {vr.name: vr for vr in run_router_matrix(tasks, default_variants(tasks), k=5, seed=0)}
    a = results["A_rule_hard"]
    b = results["B_none"]
    d = results["D_rule_fallback"]
    # No router (B) recovers recall lost to hard routing (A).
    assert b.retrieval["recall_at_k"] >= a.retrieval["recall_at_k"]
    # Global fallback (D) prevents empty results the hard router produces.
    assert d.router["empty_result_rate"] <= a.router["empty_result_rate"]
    # Stale-rate stays ~0 across variants (resolver unchanged).
    for vr in results.values():
        assert vr.retrieval["stale_memory_rate"] == 0.0
