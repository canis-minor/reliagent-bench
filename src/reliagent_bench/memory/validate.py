"""v1.3 validation: does the v1.2 router conclusion hold on a bigger benchmark?

Combines three lenses and turns them into a data-driven decision:

* **Oracle Gap** — Oracle metric minus each variant's metric (focus:
  current-state accuracy). ~0 means routing is effectively solved.
* **Failure distribution** — the target system's failures by type (count + %),
  to check whether routing remains the dominant bottleneck.
* **Stability** — the same metrics across committed benchmark versions.

Nothing here changes TypedMem, the router, or retrieval — it only measures.
"""

from __future__ import annotations

from dataclasses import dataclass

from typedmem import HashingEmbeddingProvider

from .analysis import FAILURE_TYPES, diagnose_all, failure_summary
from .baselines import DEFAULT_SYSTEMS
from .dataset import DATASET_VERSION
from .history import BENCHMARK_VERSION, build_history_record, load_history_records
from .router_experiment import default_variants, run_router_matrix, split_tasks
from .runner import run_benchmark

ORACLE = "Oracle_ceiling"
FALLBACK = "D_rule_fallback"
GAP_THRESHOLD = 0.05  # current-state gap below this = routing effectively solved
GAP_METRICS = ("current_state_accuracy", "recall_at_k", "precision_at_k")


def oracle_gap(variant_results, metric: str) -> dict[str, float]:
    by_name = {v.name: v.retrieval.get(metric, 0.0) for v in variant_results}
    o = by_name.get(ORACLE, 0.0)
    return {name: round(o - val, 4) for name, val in by_name.items()}


def failure_distribution(records) -> list[tuple[str, int, float]]:
    fs = failure_summary(records)
    total = sum(fs.values()) or 1
    return [(ft, fs[ft], fs[ft] / total) for ft in FAILURE_TYPES]


def decide(eval_variants, records, *, gap_threshold: float = GAP_THRESHOLD) -> tuple[str, str]:
    gap_d = oracle_gap(eval_variants, "current_state_accuracy").get(FALLBACK, 1.0)
    fs = failure_summary(records)
    total = sum(fs.values())
    router_pct = (fs["router"] / total) if total else 0.0
    if total and router_pct < 0.5:
        return "C", (f"router is no longer the dominant failure ({router_pct:.0%} of "
                     f"{total}); prioritize the newly dominant bottleneck")
    if gap_d <= gap_threshold:
        return "A", (f"Rule+Fallback current-state gap to Oracle is {gap_d:+.2f} "
                     f"(<= {gap_threshold}); freeze routing, move to external baselines")
    return "B", (f"Rule+Fallback trails Oracle by {gap_d:+.2f} current-state "
                 f"(> {gap_threshold}); LLM router research (E/F) is warranted")


@dataclass
class Validation:
    dataset_version: str
    num_tasks: int
    num_eval: int
    eval_variants: list
    dev_variants: list
    records: list
    failure_dist: list
    gaps: dict
    case: str
    rationale: str
    history_record: dict


def run_validation(tasks, *, k: int = 5, seed: int = 0, embedder_dim: int = 1024) -> Validation:
    dev, ev = split_tasks(tasks, eval_fraction=0.3, seed=seed)
    variants = default_variants(tasks)
    eval_variants = run_router_matrix(ev, variants, k=k, seed=seed, embedder_dim=embedder_dim)
    dev_variants = run_router_matrix(dev, variants, k=k, seed=seed, embedder_dim=embedder_dim)

    result = run_benchmark(tasks, DEFAULT_SYSTEMS, k=k, seed=seed, embedder_dim=embedder_dim)
    embedder = HashingEmbeddingProvider(dim=embedder_dim)
    records = diagnose_all(tasks, embedder, result.per_query, "typedmem", k)

    gaps = {m: oracle_gap(eval_variants, m) for m in GAP_METRICS}
    case, rationale = decide(eval_variants, records)
    return Validation(
        dataset_version=DATASET_VERSION, num_tasks=len(tasks), num_eval=len(ev),
        eval_variants=eval_variants, dev_variants=dev_variants, records=records,
        failure_dist=failure_distribution(records), gaps=gaps,
        case=case, rationale=rationale,
        history_record=build_history_record(result, records),
    )


# ── rendering ────────────────────────────────────────────────────────────────
def render_oracle_gap(v: Validation) -> str:
    variants = [vr.name for vr in v.eval_variants if vr.name != ORACLE]
    out = ["### Oracle Gap (Oracle − variant, held-out eval; lower = closer to ideal)",
           "",
           "| Variant | " + " | ".join(m.replace("_", " ") for m in GAP_METRICS) + " |",
           "|" + "---|" * (len(GAP_METRICS) + 1)]
    for name in variants:
        cells = " | ".join(f"{v.gaps[m][name]:+.2f}" for m in GAP_METRICS)
        out.append(f"| {name} | {cells} |")
    return "\n".join(out)


def render_failure_distribution(v: Validation) -> str:
    total = sum(c for _, c, _ in v.failure_dist)
    out = [f"### Failure distribution — typedmem ({total} failures over {v.num_tasks} tasks)",
           "", "| Failure type | Count | Percentage |", "|---|---:|---:|"]
    for ft, count, pct in v.failure_dist:
        out.append(f"| {ft} | {count} | {pct*100:.0f}% |")
    return "\n".join(out)


def render_stability(current: dict) -> str:
    records = load_history_records()
    # include the current run even if not yet written to disk
    key = (current.get("benchmark_version"), current.get("dataset_version"))
    if not any((r.get("benchmark_version"), r.get("dataset_version")) == key for r in records):
        records = records + [current]
    out = ["### Stability across benchmark versions (typedmem)", "",
           "| bench / dataset | tasks | Recall | Cur-state | Stale | Router-fail % |",
           "|---|---:|---:|---:|---:|---:|"]
    for r in records:
        ov = r.get("overall", {}).get("typedmem", {})
        fb = r.get("failures", {}).get("by_type", {})
        tot = sum(fb.values()) or 1
        out.append(
            f"| {r.get('benchmark_version')} / {r.get('dataset_version')} "
            f"| {r.get('num_tasks')} "
            f"| {ov.get('recall_at_k', 0):.2f} | {ov.get('current_state_accuracy', 0):.2f} "
            f"| {ov.get('stale_memory_rate', 0):.2f} | {fb.get('router', 0)/tot*100:.0f}% |"
        )
    return "\n".join(out)


def render_validation(v: Validation) -> str:
    decision_map = {
        "A": "Rule+Fallback ≈ Oracle → **freeze routing; move to external baselines (Mem0/LangMem/Zep).**",
        "B": "Rule+Fallback well below Oracle → **proceed to LLM router research (E/F).**",
        "C": "Failure attribution shifted → **prioritize the newly dominant bottleneck.**",
    }
    out = [
        "# Validation — does the routing conclusion hold at scale?",
        "",
        f"- dataset **{v.dataset_version}** · **{v.num_tasks}** tasks · held-out eval **{v.num_eval}** · benchmark **{BENCHMARK_VERSION}**",
        "- No TypedMem / router / retrieval changes — measurement only.",
        "",
        render_oracle_gap(v),
        "",
        render_failure_distribution(v),
        "",
        render_stability(v.history_record),
        "",
        "## Decision",
        "",
        f"**Case {v.case}.** {v.rationale}",
        "",
        f"→ {decision_map[v.case]}",
    ]
    return "\n".join(out)
