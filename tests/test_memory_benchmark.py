"""End-to-end benchmark run over the seed dataset."""

from reliagent_bench.memory import DEFAULT_SYSTEMS, load_tasks, run_benchmark
from reliagent_bench.memory.baselines import ABLATION_SYSTEMS
from reliagent_bench.memory.dataset import build_store


def test_frozen_manifest_matches():
    """ReliAgent Bench v1.0 freeze guard: the loaded dataset must match the
    committed FROZEN_MANIFEST.json exactly. Any change to the frozen v1.0 dataset
    (tasks, ids, content) fails here — changes require a new dataset version."""
    import json

    from reliagent_bench.memory.dataset import FROZEN_MANIFEST, dataset_fingerprint

    committed = json.loads(FROZEN_MANIFEST.read_text())
    assert dataset_fingerprint() == committed


def test_seed_dataset_loads():
    tasks = load_tasks()
    assert len(tasks) >= 100
    categories = {t.category for t in tasks}
    required = {
        "preference_evolution", "goal_evolution", "decision_retrieval",
        "temporal_updates", "entity_disambiguation", "status_tracking",
        "long_history_retrieval", "contradictions", "cross_session",
    }
    assert required <= categories   # plus routing-stress categories (implicit_goal, mixed_type)
    # Task ids are unique, and every label references a real memory id.
    assert len({t.id for t in tasks}) == len(tasks)
    for t in tasks:
        ids = {m["id"] for m in t.memories}
        assert set(t.relevant_ids) <= ids
        assert set(t.stale_ids) <= ids


def test_build_store_preserves_timeline_verbatim():
    task = next(t for t in load_tasks() if t.id == "goal-01")
    store = build_store(task)
    assert len(list(store)) == len(task.memories)   # nothing merged away
    m1 = store.get("m1")
    assert m1 is not None and m1.superseded_by == "m2"  # supersession preserved


def test_end_to_end_three_arms_run_and_are_well_formed():
    tasks = load_tasks()
    result = run_benchmark(tasks, DEFAULT_SYSTEMS, k=5, seed=0)

    # Per-query results are preserved for every (task, system).
    assert len(result.per_query) == len(tasks) * len(DEFAULT_SYSTEMS)
    assert set(result.overall) == {"vector", "vector_filter", "typedmem"}

    # Config recorded for reproducibility.
    assert result.config.seed == 0
    assert result.config.num_tasks == len(tasks)
    assert result.config.typedmem_version

    # All metrics are valid probabilities/rates.
    for q in result.per_query:
        for name, value in q.metrics.items():
            assert 0.0 <= value <= 1.0, (q.system, name, value)


def test_typedmem_never_retrieves_stale_memories():
    """The thesis-critical, deterministic invariant: temporal resolution means
    the full TypedMem arm never surfaces a superseded/stale memory, and never
    does worse than vector-only on stale-rate."""
    tasks = load_tasks()
    result = run_benchmark(tasks, DEFAULT_SYSTEMS, k=5, seed=0)
    typed_stale = result.overall["typedmem"]["stale_memory_rate"]
    vector_stale = result.overall["vector"]["stale_memory_rate"]
    assert typed_stale == 0.0
    assert typed_stale <= vector_stale


def test_runs_are_deterministic():
    tasks = load_tasks()
    a = run_benchmark(tasks, DEFAULT_SYSTEMS, k=5, seed=0).overall
    b = run_benchmark(tasks, DEFAULT_SYSTEMS, k=5, seed=0).overall
    assert a == b


def test_ablation_runs_all_stages():
    tasks = load_tasks()
    result = run_benchmark(tasks, ABLATION_SYSTEMS, k=5, seed=0)
    assert set(result.overall) == {"vector", "+filters", "+resolver", "full"}
    # Adding the resolver should not increase the stale-rate over filters-only.
    assert result.overall["+resolver"]["stale_memory_rate"] <= result.overall["+filters"]["stale_memory_rate"]
