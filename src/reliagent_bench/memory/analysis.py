"""Failure analysis — a first-class benchmark artifact.

For each task the target system got wrong, we replay the public TypedMem stages
and locate *where* the correct memory dropped out, then label the failure:

* `router`    — the type filter removed the relevant memory (routing/filter).
* `embedding` — the relevant memory never entered the vector candidate set.
* `temporal`  — the resolver removed the current memory (mislabeled supersession).
* `entity`    — top result belongs to the wrong entity.
* `ranking`   — the relevant memory was retrieved but ranked below the cutoff.
* `unknown`   — none of the above; needs manual investigation.

Nothing here modifies TypedMem — it only *calls* the public stage functions to
attribute blame, which doubles as a per-stage contribution estimate.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass

from typedmem.embeddings import EmbeddingProvider
from typedmem.retrieval import (
    MemoryVectorizer,
    apply_filters,
    build_filters,
    resolve_temporal,
    route_query,
    search_candidates,
)

from .baselines import CANDIDATE_K, _single_valued_types
from .dataset import MemoryTask, build_store

FAILURE_TYPES = ["router", "entity", "embedding", "temporal", "ranking", "unknown"]

# Which pipeline stage each failure type implicates (for stage-contribution).
STAGE_OF_FAILURE = {
    "router": "router / typed filters",
    "embedding": "vector candidate retrieval",
    "temporal": "temporal resolver",
    "entity": "router / entity resolution",
    "ranking": "reranker",
    "unknown": "unknown",
}


@dataclass
class FailureRecord:
    task_id: str
    category: str
    difficulty: str
    query: str
    expected: list[str]
    retrieved: list[str]
    failure_type: str
    root_cause: str
    possible_fix: str


def is_failure(task: MemoryTask, retrieved: list[str], k: int) -> bool:
    """A failure = the top result is not a current/relevant memory, or a stale
    memory was surfaced in the top-k."""
    top = retrieved[:k]
    current_ok = bool(top) and top[0] in task.relevant
    stale_hit = any(x in task.stale for x in top)
    return (not current_ok) or stale_hit


def diagnose(
    task: MemoryTask,
    embedder: EmbeddingProvider,
    retrieved: list[str],
    k: int,
) -> FailureRecord | None:
    """Classify a single target-system failure. Returns None if not a failure."""
    if not is_failure(task, retrieved, k):
        return None

    def record(ftype: str, cause: str, fix: str) -> FailureRecord:
        return FailureRecord(
            task_id=task.id, category=task.category, difficulty=task.eff_difficulty(),
            query=task.query, expected=sorted(task.relevant), retrieved=retrieved,
            failure_type=ftype, root_cause=cause, possible_fix=fix,
        )

    store = build_store(task)
    all_mems = list(store)
    relevant = task.relevant

    intent = route_query(task.query)
    filters = build_filters(intent, workspace=store.default_workspace)
    pool = apply_filters(all_mems, filters)
    pool_ids = {m.id for m in pool}
    if relevant and not (relevant & pool_ids):
        return record(
            "router",
            f"router predicted types {intent.memory_types}; the type filter "
            f"dropped the relevant {task.eff_expected_memory_type()!r} memory",
            "improve query routing (do not over-filter to a single type)",
        )

    vz = MemoryVectorizer(embedder)
    cands = search_candidates(task.query, pool, embedder=embedder, vectorizer=vz, top_k=CANDIDATE_K)
    cand_ids = {c.memory.id for c in cands}
    if relevant and not (relevant & cand_ids):
        return record(
            "embedding",
            "the relevant memory never entered the vector candidate set",
            "use a stronger embedder or a larger candidate_k",
        )

    resolved = resolve_temporal(
        [c.memory for c in cands], collapse_types=_single_valued_types(store),
    )
    resolved_ids = {m.id for m in resolved}
    if relevant and not (relevant & resolved_ids):
        return record(
            "temporal",
            "the temporal resolver removed the current memory "
            "(supersession/timestamps may be mislabeled)",
            "review superseded_by labels and the resolver's slot-collapse rule",
        )

    top = retrieved[:k]
    if task.expected_entity is not None:
        subj = {m["id"]: m.get("subject") for m in task.memories}
        if not top or subj.get(top[0]) != task.expected_entity:
            return record(
                "entity",
                f"top result belongs to the wrong entity (expected {task.expected_entity!r})",
                "add entity resolution to routing/filters",
            )

    return record(
        "ranking",
        "the relevant memory survived to ranking but was ranked below the cutoff",
        "tune the reranker (semantic/recency/type weights)",
    )


def diagnose_all(
    tasks: list[MemoryTask],
    embedder: EmbeddingProvider,
    per_query,
    system: str,
    k: int,
) -> list[FailureRecord]:
    """Diagnose every failing task for one system from a benchmark run."""
    by_task = {q.task_id: q for q in per_query if q.system == system}
    records: list[FailureRecord] = []
    for task in tasks:
        q = by_task.get(task.id)
        if q is None:
            continue
        rec = diagnose(task, embedder, q.retrieved_ids, task.top_k or k)
        if rec is not None:
            records.append(rec)
    return records


def failure_summary(records: list[FailureRecord]) -> dict[str, int]:
    counts = Counter(r.failure_type for r in records)
    return {ft: counts.get(ft, 0) for ft in FAILURE_TYPES}


def stage_contribution(records: list[FailureRecord]) -> dict[str, int]:
    counts: Counter = Counter(STAGE_OF_FAILURE[r.failure_type] for r in records)
    return dict(counts)


def category_improvement(result, metric: str = "current_state_accuracy",
                         baseline: str = "vector", target: str = "typedmem") -> list[dict]:
    """Per-category baseline vs. target on ``metric``, with the delta."""
    rows: list[dict] = []
    for category in sorted(result.per_category):
        b = result.per_category[category].get(baseline, {}).get(metric, 0.0)
        t = result.per_category[category].get(target, {}).get(metric, 0.0)
        rows.append({"category": category, baseline: b, target: t, "improvement": t - b})
    return rows


def records_to_dicts(records: list[FailureRecord]) -> list[dict]:
    return [asdict(r) for r in records]


# ── rendering ──────────────────────────────────────────────────────────────
def render_category_improvement(result, metric: str = "current_state_accuracy") -> str:
    systems = result.config.systems
    baseline, target = systems[0], systems[-1]
    rows = category_improvement(result, metric=metric, baseline=baseline, target=target)
    out = [
        f"### Category breakdown — {metric} ({baseline} → {target})",
        "",
        f"| Category | {baseline} | {target} | Improvement |",
        "|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f"| {r['category']} | {r[baseline]:.2f} | {r[target]:.2f} | {r['improvement']:+.2f} |"
        )
    return "\n".join(out)


def render_failure_report(records: list[FailureRecord], *, target: str) -> str:
    fs = failure_summary(records)
    out = [
        f"# Failure analysis — `{target}`",
        "",
        f"Total failures: **{len(records)}**",
        "",
        "| Failure type | Count |",
        "|---|---:|",
    ]
    for ft in FAILURE_TYPES:
        out.append(f"| {ft} | {fs[ft]} |")
    out += ["", "### Stage contribution", "", "| Stage | Failures |", "|---|---:|"]
    for stage, n in sorted(stage_contribution(records).items(), key=lambda x: -x[1]):
        out.append(f"| {stage} | {n} |")
    out += ["", "### Cases", ""]
    for r in records:
        out += [
            f"- **{r.task_id}** ({r.category} · {r.difficulty}) — “{r.query}”",
            f"  - failure_type: `{r.failure_type}`",
            f"  - expected: `{r.expected}` · retrieved: `{r.retrieved}`",
            f"  - root_cause: {r.root_cause}",
            f"  - possible_fix: {r.possible_fix}",
        ]
    return "\n".join(out)
