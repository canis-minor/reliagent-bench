"""v1.5 cross-system: audit, agnostic failure classification, comparison, registry."""

from reliagent_bench.memory import (
    available_external_names,
    available_systems,
    builtin_systems,
    classify_failure,
    load_tasks,
    run_audit,
    run_comparison,
)
from reliagent_bench.memory.dataset import MemoryTask


def _task(relevant, stale=(), expected_entity=None, memories=None):
    memories = memories or [
        {"id": "m1", "type": "fact", "subject": "s", "content": "a"},
        {"id": "m2", "type": "fact", "subject": "s", "content": "b"},
    ]
    return MemoryTask(id="t", category="temporal_updates", query="q?",
                      memories=memories, relevant_ids=list(relevant),
                      stale_ids=list(stale), expected_entity=expected_entity)


# ── system-agnostic failure classification ─────────────────────────────────
def test_classify_failure_labels():
    t = _task(relevant=["m2"], stale=["m1"])
    assert classify_failure(t, ["m2"], 5) is None          # answered
    assert classify_failure(t, ["m1", "m2"], 5) == "stale"  # stale surfaced
    assert classify_failure(t, ["x", "y"], 5) == "missed"   # relevant never retrieved
    assert classify_failure(t, ["m1"], 5) == "stale"        # top-1 stale


def test_classify_failure_mis_ranked_and_entity():
    t = _task(relevant=["m2"], stale=[])
    # relevant present but not top-1, no stale → mis_ranked
    assert classify_failure(t, ["x", "m2"], 5) == "mis_ranked"
    ent = _task(relevant=["m1"], expected_entity="s1",
                memories=[{"id": "m1", "type": "fact", "subject": "s1", "content": "a"},
                          {"id": "m2", "type": "fact", "subject": "s2", "content": "b"}])
    assert classify_failure(ent, ["m2", "m1"], 5) == "entity"  # wrong entity on top


# ── audit ───────────────────────────────────────────────────────────────────
def test_audit_fairness_and_shape():
    a = run_audit(load_tasks())
    assert a.num_tasks == 104
    assert all(a.fairness_invariants.values())      # all invariants hold
    assert a.non_questions == []                    # every query is a question
    assert isinstance(a.type_leakage, list)         # surfaced, not asserted-zero


# ── comparison + registry ────────────────────────────────────────────────────
def test_registry_builtin_only_here():
    # No external packages/keys in CI → only built-ins are available.
    assert [n for n, _ in builtin_systems()] == ["vector", "vector_filter", "typedmem"]
    assert available_external_names() == []
    assert [n for n, _ in available_systems()] == ["vector", "vector_filter", "typedmem"]


def test_run_comparison_structure_and_heatmap():
    tasks = load_tasks()
    c = run_comparison(builtin_systems(), tasks, k=5, seed=0)
    by = {s.name: s for s in c.systems}
    assert set(by) == {"vector", "vector_filter", "typedmem"}
    # TypedMem never surfaces a stale memory; vector does.
    assert by["typedmem"].failures["stale"] == 0
    assert by["vector"].failures["stale"] > 0
    # leaderboard covers every category; environment carries repro metadata
    assert len(by["typedmem"].per_category) == len({t.category for t in tasks})
    for key in ("benchmark_version", "dataset_version", "embedder", "seed", "external_packages"):
        assert key in c.environment
