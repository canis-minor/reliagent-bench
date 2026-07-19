"""Memory-retrieval benchmark track for ReliAgent Bench.

Compares three retrieval arms — vector-only, vector + typed filters, and the full
TypedMem pipeline — on the same hand-labeled tasks, with per-query results for
error analysis. Depends on TypedMem's public API only; TypedMem does not depend
on this package.
"""

from .baselines import (
    ABLATION_SYSTEMS,
    DEFAULT_SYSTEMS,
    FilteredVectorRetriever,
    TypedMemRetriever,
    VectorRetriever,
)
from .dataset import DEFAULT_DATASET, MemoryTask, build_store, load_tasks
from .evaluator import evaluate_query, mean_metrics
from .runner import BenchmarkResult, QueryResult, RunConfig, run_benchmark

__all__ = [
    "ABLATION_SYSTEMS",
    "DEFAULT_SYSTEMS",
    "BenchmarkResult",
    "DEFAULT_DATASET",
    "FilteredVectorRetriever",
    "MemoryTask",
    "QueryResult",
    "RunConfig",
    "TypedMemRetriever",
    "VectorRetriever",
    "build_store",
    "evaluate_query",
    "load_tasks",
    "mean_metrics",
    "run_benchmark",
]
