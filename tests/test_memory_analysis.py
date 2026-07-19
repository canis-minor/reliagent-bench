"""v1.1: structured metadata, difficulty, failure classification, history."""

from typedmem import HashingEmbeddingProvider

from reliagent_bench.memory import (
    DEFAULT_SYSTEMS,
    build_history_record,
    diagnose,
    diagnose_all,
    failure_summary,
    is_failure,
    load_tasks,
    run_benchmark,
)
from reliagent_bench.memory.dataset import MemoryTask


def _task(**kw) -> MemoryTask:
    base = dict(id="t", category="temporal_updates", query="q",
                memories=[{"id": "m1", "type": "fact", "content": "x"}],
                relevant_ids=["m1"], stale_ids=[])
    base.update(kw)
    return MemoryTask(**base)


# ── metadata derivation ────────────────────────────────────────────────────
def test_metadata_derives_when_unspecified():
    t = _task(
        category="preference_evolution",
        memories=[
            {"id": "m1", "type": "preference", "subject": "s", "content": "a", "superseded_by": "m2"},
            {"id": "m2", "type": "preference", "subject": "s", "content": "b"},
        ],
        relevant_ids=["m2"], stale_ids=["m1"],
    )
    md = t.metadata()
    assert md["requires_temporal_resolution"] is True   # supersession present
    assert md["requires_entity_resolution"] is False
    assert md["expected_memory_type"] == "preference"
    assert md["difficulty"] == "medium"                 # temporal evolution
    assert "temporal" in md["required_capabilities"]


def test_metadata_easy_and_hard():
    easy = _task()  # single memory, no stale
    assert easy.metadata()["difficulty"] == "easy"
    hard = _task(category="long_history_retrieval",
                 memories=[{"id": f"m{i}", "type": "fact", "content": str(i)} for i in range(7)],
                 relevant_ids=["m0"])
    assert hard.metadata()["difficulty"] == "hard"


def test_explicit_metadata_overrides_derivation():
    t = _task(difficulty="hard", requires_entity_resolution=True)
    md = t.metadata()
    assert md["difficulty"] == "hard"
    assert md["requires_entity_resolution"] is True


# ── failure classification ─────────────────────────────────────────────────
def test_is_failure():
    t = _task(relevant_ids=["m1"], stale_ids=["s1"])
    assert is_failure(t, ["m1"], k=5) is False
    assert is_failure(t, ["x"], k=5) is True        # top-1 not relevant
    assert is_failure(t, ["m1", "s1"], k=5) is True  # stale surfaced


def test_router_over_filtering_is_diagnosed():
    """goal-03's query starts with 'What is', which the v0 router maps to
    'fact'; the type filter then drops the goal memories -> router failure."""
    task = next(t for t in load_tasks() if t.id == "goal-03")
    embedder = HashingEmbeddingProvider(dim=1024)
    rec = diagnose(task, embedder, retrieved=[], k=5)
    assert rec is not None
    assert rec.failure_type == "router"
    assert rec.possible_fix


def test_success_task_diagnoses_to_none():
    task = next(t for t in load_tasks() if t.id == "temp-01")
    embedder = HashingEmbeddingProvider(dim=1024)
    # temp-01: typedmem returns the current memory -> not a failure.
    rec = diagnose(task, embedder, retrieved=["m2"], k=5)
    assert rec is None


def test_diagnose_all_and_summary_on_real_run():
    tasks = load_tasks()
    result = run_benchmark(tasks, DEFAULT_SYSTEMS, k=5, seed=0)
    embedder = HashingEmbeddingProvider(dim=1024)
    records = diagnose_all(tasks, embedder, result.per_query, "typedmem", 5)
    summary = failure_summary(records)
    assert sum(summary.values()) == len(records)
    # The known router over-filtering failures should be present.
    assert summary["router"] >= 1


# ── history record ─────────────────────────────────────────────────────────
def test_history_record_has_reproducibility_fields():
    tasks = load_tasks()
    result = run_benchmark(tasks, DEFAULT_SYSTEMS, k=5, seed=0)
    rec = build_history_record(result, [])
    for key in ("benchmark_version", "dataset_version", "typedmem_version",
                "config", "overall", "failures"):
        assert key in rec
    assert rec["config"]["seed"] == 0
    assert set(rec["failures"]) == {"total", "by_type"}
