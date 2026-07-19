"""Benchmark runner.

Executes every retrieval arm against the SAME per-task store, query, embedder,
and top_k, and records PER-QUERY results (not just aggregates) so error analysis
is possible. Runs are deterministic: the embedder is a pure hash and the seed +
full configuration are recorded on the result.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import asdict, dataclass, field

import typedmem
from typedmem import HashingEmbeddingProvider

from .baselines import DEFAULT_SYSTEMS, SystemFactory
from .dataset import MemoryTask, build_store, subject_map
from .evaluator import evaluate_query, mean_metrics


@dataclass
class RunConfig:
    k: int
    seed: int
    embedder_id: str
    embedder_dim: int
    typedmem_version: str
    dataset: str
    num_tasks: int
    systems: list[str]


@dataclass
class QueryResult:
    task_id: str
    category: str
    system: str
    query: str
    retrieved_ids: list[str]
    metrics: dict[str, float]


@dataclass
class BenchmarkResult:
    config: RunConfig
    per_query: list[QueryResult] = field(default_factory=list)
    overall: dict[str, dict[str, float]] = field(default_factory=dict)
    per_category: dict[str, dict[str, dict[str, float]]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "config": asdict(self.config),
            "overall": self.overall,
            "per_category": self.per_category,
            "per_query": [asdict(q) for q in self.per_query],
        }


def run_benchmark(
    tasks: list[MemoryTask],
    systems: list[tuple[str, SystemFactory]] | None = None,
    *,
    k: int = 5,
    seed: int = 0,
    embedder_dim: int = 1024,
    dataset_name: str = "seed",
) -> BenchmarkResult:
    systems = systems if systems is not None else DEFAULT_SYSTEMS
    random.seed(seed)  # reserved; the pipeline is deterministic today
    embedder = HashingEmbeddingProvider(dim=embedder_dim)

    per_query: list[QueryResult] = []
    for task in tasks:
        store = build_store(task)
        subjects = subject_map(task)
        top_k = task.top_k or k
        for name, factory in systems:
            adapter = factory(store, embedder)
            retrieved = adapter.retrieve(task.query, top_k)
            metrics = evaluate_query(task, retrieved, top_k, subjects)
            per_query.append(QueryResult(
                task_id=task.id, category=task.category, system=name,
                query=task.query, retrieved_ids=list(retrieved), metrics=metrics,
            ))

    overall = _aggregate(per_query, key=lambda q: (q.system,))
    overall = {sys: m for (sys,), m in overall.items()}

    per_cat_raw = _aggregate(per_query, key=lambda q: (q.category, q.system))
    per_category: dict[str, dict[str, dict[str, float]]] = defaultdict(dict)
    for (category, sys), m in per_cat_raw.items():
        per_category[category][sys] = m

    config = RunConfig(
        k=k, seed=seed, embedder_id=embedder.id, embedder_dim=embedder_dim,
        typedmem_version=typedmem.__version__, dataset=dataset_name,
        num_tasks=len(tasks), systems=[n for n, _ in systems],
    )
    return BenchmarkResult(
        config=config, per_query=per_query,
        overall=overall, per_category=dict(per_category),
    )


def _aggregate(per_query, key):
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for q in per_query:
        buckets[key(q)].append(q.metrics)
    return {k: mean_metrics(v) for k, v in buckets.items()}
