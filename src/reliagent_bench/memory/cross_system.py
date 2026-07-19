"""Stage 1+ — cross-system comparison on the frozen benchmark.

Runs any set of retrievers (built-in or external adapters) over the same tasks,
same evaluator, same top-k, and produces a category leaderboard and a
**system-agnostic failure heatmap**. Failure attribution here uses only
(retrieved, relevant, stale) — no pipeline introspection — so it applies equally
to a glass-box system (TypedMem) and a black-box one (Mem0/LangMem/Zep).
"""

from __future__ import annotations

import platform
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from typedmem import HashingEmbeddingProvider

from .dataset import MemoryTask, build_store, load_tasks, subject_map
from .evaluator import evaluate_query, mean_metrics

# System-agnostic failure taxonomy (computed from outputs alone).
AGNOSTIC_FAILURES = ["stale", "missed", "entity", "mis_ranked"]

LEADERBOARD_METRIC = "current_state_accuracy"


def classify_failure(task: MemoryTask, retrieved: list[str], k: int) -> str | None:
    """Return a system-agnostic failure label, or None if the task was answered.
    Answered = top-1 is relevant AND no stale in top-k."""
    top = retrieved[:k]
    stale_hit = any(x in task.stale for x in top)
    top1_relevant = bool(top) and top[0] in task.relevant
    any_relevant = any(x in task.relevant for x in top)
    if not stale_hit and top1_relevant:
        return None
    if stale_hit:
        return "stale"                      # surfaced an out-of-date memory
    if not any_relevant:
        return "missed"                     # relevant memory never retrieved
    if task.expected_entity is not None:
        subj = subject_map(task)
        if not top or subj.get(top[0]) != task.expected_entity:
            return "entity"                 # wrong entity on top
    return "mis_ranked"                     # relevant retrieved but not ranked first


@dataclass
class SystemResult:
    name: str
    overall: dict[str, float]
    per_category: dict[str, dict[str, float]]
    failures: dict[str, int]
    per_query: list[dict] = field(default_factory=list)


@dataclass
class Comparison:
    systems: list[SystemResult]
    environment: dict
    num_tasks: int


# ── built-in systems (glass-box, always runnable) ──────────────────────────
def builtin_systems():
    from .baselines import FilteredVectorRetriever, TypedMemRetriever, VectorRetriever

    def prep(cls):
        def build(task, embedder):
            r = cls(build_store(task), embedder)
            return r.retrieve
        return build

    return [
        ("vector", prep(VectorRetriever)),
        ("vector_filter", prep(FilteredVectorRetriever)),
        ("typedmem", prep(TypedMemRetriever)),
    ]


def run_comparison(
    systems,
    tasks: list[MemoryTask] | None = None,
    *,
    k: int = 5,
    seed: int = 0,
    embedder_dim: int = 1024,
) -> Comparison:
    tasks = tasks if tasks is not None else load_tasks()
    embedder = HashingEmbeddingProvider(dim=embedder_dim)

    results: list[SystemResult] = []
    for name, build in systems:
        retr_dicts: list[dict] = []
        cat_dicts: dict[str, list[dict]] = defaultdict(list)
        fails: Counter = Counter()
        per_query: list[dict] = []
        for task in tasks:
            tk = task.top_k or k
            retrieve = build(task, embedder)
            got = list(retrieve(task.query, tk))
            m = evaluate_query(task, got, tk, subject_map(task))
            retr_dicts.append(m)
            cat_dicts[task.category].append(m)
            f = classify_failure(task, got, tk)
            if f is not None:
                fails[f] += 1
            per_query.append({"task_id": task.id, "category": task.category,
                              "retrieved": got, "metrics": m, "failure": f})
        results.append(SystemResult(
            name=name,
            overall=mean_metrics(retr_dicts),
            per_category={c: mean_metrics(v) for c, v in cat_dicts.items()},
            failures={ft: fails.get(ft, 0) for ft in AGNOSTIC_FAILURES},
            per_query=per_query,
        ))

    return Comparison(systems=results, environment=_environment(seed, k, embedder), num_tasks=len(tasks))


def _environment(seed: int, k: int, embedder) -> dict:
    import typedmem

    from .dataset import DATASET_VERSION
    from .history import BENCHMARK_VERSION, _git_commit, REPO_ROOT

    return {
        "benchmark_version": BENCHMARK_VERSION,
        "dataset_version": DATASET_VERSION,
        "reliagent_commit": _git_commit(REPO_ROOT),
        "typedmem_version": typedmem.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "embedder": embedder.id,
        "k": k,
        "seed": seed,
        "external_packages": _external_versions(),
    }


def _external_versions() -> dict:
    import importlib.metadata as im
    out = {}
    for pkg in ("mem0ai", "langmem", "zep-python", "zep-cloud"):
        try:
            out[pkg] = im.version(pkg)
        except im.PackageNotFoundError:
            out[pkg] = None
    return out


# ── rendering ──────────────────────────────────────────────────────────────
_OVERALL_COLS = [
    ("Recall", "recall_at_k"), ("Prec", "precision_at_k"), ("MRR", "mrr"),
    ("NDCG", "ndcg_at_k"), ("Stale", "stale_memory_rate"), ("Cur-state", "current_state_accuracy"),
]


def render_overall(c: Comparison) -> str:
    out = ["### Overall", "", "| System | " + " | ".join(l for l, _ in _OVERALL_COLS) + " |",
           "|" + "---|" * (len(_OVERALL_COLS) + 1)]
    for s in c.systems:
        cells = " | ".join(f"{s.overall.get(key, 0):.2f}" for _, key in _OVERALL_COLS)
        out.append(f"| {s.name} | {cells} |")
    return "\n".join(out)


def render_leaderboard(c: Comparison) -> str:
    cats = sorted({cat for s in c.systems for cat in s.per_category})
    out = [f"### Category leaderboard ({LEADERBOARD_METRIC})", "",
           "| Category | " + " | ".join(s.name for s in c.systems) + " |",
           "|" + "---|" * (len(c.systems) + 1)]
    for cat in cats:
        cells = " | ".join(f"{s.per_category.get(cat, {}).get(LEADERBOARD_METRIC, 0):.2f}" for s in c.systems)
        out.append(f"| {cat} | {cells} |")
    return "\n".join(out)


def render_heatmap(c: Comparison) -> str:
    out = ["### Failure heatmap (system-agnostic; counts, lower is better)", "",
           "| System | " + " | ".join(AGNOSTIC_FAILURES) + " | total |",
           "|" + "---|" * (len(AGNOSTIC_FAILURES) + 2)]
    for s in c.systems:
        cells = " | ".join(str(s.failures[f]) for f in AGNOSTIC_FAILURES)
        out.append(f"| {s.name} | {cells} | {sum(s.failures.values())} |")
    return "\n".join(out)


def render_comparison(c: Comparison) -> str:
    e = c.environment
    ext = ", ".join(f"{k}={v}" for k, v in e["external_packages"].items() if v) or "none installed"
    out = [
        "# Cross-system comparison (ReliAgent Bench v1.0)",
        "",
        f"- systems: **{', '.join(s.name for s in c.systems)}** · tasks: **{c.num_tasks}** · "
        f"k={e['k']} · seed={e['seed']} · embedder `{e['embedder']}`",
        f"- benchmark {e['benchmark_version']} · dataset {e['dataset_version']} · "
        f"typedmem {e['typedmem_version']} · python {e['python']}",
        f"- external memory packages: {ext}",
        "",
        render_overall(c), "",
        render_leaderboard(c), "",
        render_heatmap(c), "",
        "> Failure labels are computed from outputs only (stale surfaced / relevant missed / "
        "wrong entity / relevant mis-ranked), so they apply to any system — glass-box or black-box.",
    ]
    return "\n".join(out)
