"""Router experiment: benchmark matrix over routing strategies.

Held-out split (dev/eval), the same retrieval + router metrics for every variant,
refined router-failure attribution, and a matrix report. Only routing varies —
the resolver and ranker are fixed.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from typedmem import HashingEmbeddingProvider

from .analysis import is_failure
from .dataset import MemoryTask, build_store, subject_map
from .evaluator import evaluate_query, mean_metrics
from .router_pipeline import RouterPipelineRetriever
from .routers import NoRouter, OracleRouter, RuleRouter, SoftRuleRouter

ROUTER_FAILURE_SUBTYPES = [
    "overly_narrow", "wrong_type", "no_route", "correct_route_empty", "ambiguous",
]


def split_tasks(tasks: list[MemoryTask], *, eval_fraction: float = 0.3, seed: int = 0):
    """Deterministic, category-stratified dev/eval split. Every category
    contributes at least one task to the eval set."""
    rng = random.Random(seed)
    by_cat: dict[str, list[MemoryTask]] = defaultdict(list)
    for t in tasks:
        by_cat[t.category].append(t)
    dev: list[MemoryTask] = []
    ev: list[MemoryTask] = []
    for cat in sorted(by_cat):
        items = sorted(by_cat[cat], key=lambda x: x.id)
        rng.shuffle(items)
        n_eval = max(1, round(len(items) * eval_fraction))
        ev.extend(items[:n_eval])
        dev.extend(items[n_eval:])
    return dev, ev


def router_metrics(task: MemoryTask, diag: dict) -> dict[str, float]:
    expected = set(task.relevant_types())     # all relevant types (mixed-type aware)
    predicted = set(diag["predicted_types"])
    rm: dict[str, float] = {
        "num_searched_types": float(diag["num_searched_types"]),
        "empty_result_rate": 1.0 if diag["empty_result"] else 0.0,
        "fallback_rate": 1.0 if diag["fallback_used"] else 0.0,
    }
    if expected:
        rm["exact_type_accuracy"] = 1.0 if predicted == expected else 0.0
        # acceptable if every relevant type is covered, or no filter at all
        rm["acceptable_type_recall"] = 1.0 if (expected <= predicted or not predicted) else 0.0
        rm["candidate_exclusion_rate"] = 1.0 if (predicted and not expected <= predicted) else 0.0
    return rm


def router_failure_subtype(task: MemoryTask, diag: dict) -> str:
    predicted = set(diag["predicted_types"])
    expected = set(task.relevant_types())
    if not predicted:
        return "no_route"
    if expected and not expected <= predicted:
        return "overly_narrow" if len(predicted) == 1 else "wrong_type"
    if diag["empty_result"]:
        return "correct_route_empty"
    return "ambiguous"


@dataclass
class VariantResult:
    name: str
    retrieval: dict[str, float]
    router: dict[str, float]
    operational: dict
    failure_subtypes: dict[str, int]
    per_query: list[dict] = field(default_factory=list)


def run_variant(name, router, tasks, embedder, *, k, global_fallback, meta) -> VariantResult:
    retr_dicts: list[dict] = []
    router_dicts: list[dict] = []
    subtypes: Counter = Counter()
    per_query: list[dict] = []
    for task in tasks:
        store = build_store(task)
        r = RouterPipelineRetriever(store, embedder, router, global_fallback=global_fallback)
        tk = task.top_k or k
        retrieved = r.retrieve(task.query, tk)
        rmet = evaluate_query(task, retrieved, tk, subject_map(task))
        rrm = router_metrics(task, r.diagnostics)
        retr_dicts.append(rmet)
        router_dicts.append(rrm)
        failed = is_failure(task, retrieved, tk)
        if failed:
            subtypes[router_failure_subtype(task, r.diagnostics)] += 1
        per_query.append({
            "task_id": task.id, "category": task.category, "difficulty": task.eff_difficulty(),
            "predicted_types": r.diagnostics["predicted_types"], "retrieved": retrieved,
            "failed": failed, "metrics": rmet, "router_metrics": rrm,
        })
    operational = {
        "uses_llm": any(pq["router_metrics"].get("uses_llm", 0) for pq in per_query) or meta.get("uses_llm", False),
        "external_deps": meta.get("external_deps", 0),
        "deterministic": meta.get("deterministic", True),
        "llm_calls": getattr(router, "calls", 0),
    }
    return VariantResult(
        name=name,
        retrieval=mean_metrics(retr_dicts),
        router=mean_metrics(router_dicts),
        operational=operational,
        failure_subtypes={s: subtypes.get(s, 0) for s in ROUTER_FAILURE_SUBTYPES},
        per_query=per_query,
    )


def default_variants(all_tasks: list[MemoryTask]):
    """The offline, deterministic variants (A, B, C, D, Oracle). E (LLM) and
    F (Hybrid) require an LLM client / cache and are excluded here — see routers.py."""
    oracle = OracleRouter.from_tasks(all_tasks)
    zero = {"external_deps": 0, "deterministic": True, "uses_llm": False}
    return [
        ("A_rule_hard", RuleRouter(), False, zero),
        ("B_none", NoRouter(), False, zero),
        ("C_soft_top2", SoftRuleRouter(2), False, zero),
        ("D_rule_fallback", RuleRouter(), True, zero),
        ("Oracle_ceiling", oracle, False, zero),
    ]


def run_router_matrix(tasks, variants, *, k: int = 5, seed: int = 0, embedder_dim: int = 1024):
    embedder = HashingEmbeddingProvider(dim=embedder_dim)
    return [
        run_variant(name, router, tasks, embedder, k=k, global_fallback=fb, meta=meta)
        for (name, router, fb, meta) in variants
    ]


# ── report ─────────────────────────────────────────────────────────────────
def _row(vr: VariantResult) -> str:
    r, rt = vr.retrieval, vr.router
    return (
        f"| {vr.name} "
        f"| {r.get('recall_at_k', 0):.2f} | {r.get('precision_at_k', 0):.2f} "
        f"| {r.get('current_state_accuracy', 0):.2f} | {r.get('stale_memory_rate', 0):.2f} "
        f"| {rt.get('acceptable_type_recall', 0):.2f} | {rt.get('candidate_exclusion_rate', 0):.2f} "
        f"| {rt.get('empty_result_rate', 0):.2f} | {rt.get('num_searched_types', 0):.2f} |"
    )


def render_matrix(results: list[VariantResult], *, title: str) -> str:
    out = [f"### {title}", "",
           "| Variant | Recall | Prec | Cur-state | Stale | AccTypeRecall | ExclRate | EmptyRate | AvgTypes |",
           "|---|---|---|---|---|---|---|---|---|"]
    out += [_row(vr) for vr in results]
    out += ["", "Router-failure subtypes:", "",
            "| Variant | " + " | ".join(ROUTER_FAILURE_SUBTYPES) + " |",
            "|" + "---|" * (len(ROUTER_FAILURE_SUBTYPES) + 1)]
    for vr in results:
        cells = " | ".join(str(vr.failure_subtypes[s]) for s in ROUTER_FAILURE_SUBTYPES)
        out.append(f"| {vr.name} | {cells} |")
    return "\n".join(out)


def render_report(dev_results, eval_results, *, k, seed, num_dev, num_eval) -> str:
    out = [
        "# Router experiment — benchmark matrix",
        "",
        f"- dev tasks: **{num_dev}** · eval (held-out) tasks: **{num_eval}** · k={k} · seed={seed}",
        "- Only routing varies; resolver + ranker fixed. Higher is better except "
        "Stale / ExclRate / EmptyRate.",
        "- Variants E (LLM) and F (Hybrid) require an LLM client/cache and are not in this offline run.",
        "",
        render_matrix(eval_results, title="Held-out evaluation set (the honest comparison)"),
        "",
        render_matrix(dev_results, title="Development set"),
        "",
        "> `Oracle_ceiling` routes each query to its labeled type — an upper bound "
        "for what perfect routing could achieve, not a deployable router.",
    ]
    return "\n".join(out)
