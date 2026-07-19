"""v1.3 validation: multi-type oracle, Oracle Gap, failure distribution, decision."""

from reliagent_bench.memory import load_tasks, oracle_gap, run_validation
from reliagent_bench.memory.router_experiment import default_variants, run_router_matrix
from reliagent_bench.memory.validate import FALLBACK, ORACLE


def test_relevant_types_multi():
    task = next(t for t in load_tasks() if t.id == "mixed-01")
    assert set(task.relevant_types()) == {"fact", "goal"}   # answer spans two types


def test_oracle_router_covers_all_relevant_types():
    from reliagent_bench.memory.routers import OracleRouter
    tasks = load_tasks()
    oracle = OracleRouter.from_tasks(tasks)
    mixed = next(t for t in tasks if t.id == "mixed-01")
    assert set(oracle.route(mixed.query).types) == {"fact", "goal"}


def test_oracle_gap_zero_for_oracle_variant():
    tasks = load_tasks()
    variants = run_router_matrix(tasks, default_variants(tasks), k=5, seed=0)
    gap = oracle_gap(variants, "current_state_accuracy")
    assert gap[ORACLE] == 0.0
    # Rule + fallback should be at (or very near) the Oracle ceiling.
    assert gap[FALLBACK] <= 0.05


def test_run_validation_structure_and_decision():
    tasks = load_tasks()
    v = run_validation(tasks, k=5, seed=0)
    assert v.num_tasks == len(tasks)
    assert v.case in {"A", "B", "C"}
    assert v.rationale
    # failure distribution counts sum to the number of diagnosed failures
    assert sum(c for _, c, _ in v.failure_dist) == len(v.records)
    # every gap metric present for every variant
    for metric, gaps in v.gaps.items():
        assert FALLBACK in gaps and ORACLE in gaps


def test_hard_router_trails_oracle_but_fallback_matches():
    tasks = load_tasks()
    variants = run_router_matrix(tasks, default_variants(tasks), k=5, seed=0)
    gap = oracle_gap(variants, "recall_at_k")
    assert gap["A_rule_hard"] >= gap[FALLBACK]   # hard routing costs recall; fallback recovers it
