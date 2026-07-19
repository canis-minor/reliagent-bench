"""Memory-retrieval benchmark track for ReliAgent Bench.

Compares three retrieval arms — vector-only, vector + typed filters, and the full
TypedMem pipeline — on the same hand-labeled tasks, with per-query results for
error analysis. Depends on TypedMem's public API only; TypedMem does not depend
on this package.
"""

from .analysis import (
    FailureRecord,
    category_improvement,
    diagnose,
    diagnose_all,
    failure_summary,
    is_failure,
    stage_contribution,
)
from .baselines import (
    ABLATION_SYSTEMS,
    DEFAULT_SYSTEMS,
    FilteredVectorRetriever,
    TypedMemRetriever,
    VectorRetriever,
)
from .dataset import DATASET_VERSION, DEFAULT_DATASET, MemoryTask, build_store, load_tasks
from .evaluator import evaluate_query, mean_metrics
from .history import BENCHMARK_VERSION, build_history_record, write_run_artifacts
from .runner import BenchmarkResult, QueryResult, RunConfig, run_benchmark

__all__ = [
    "ABLATION_SYSTEMS",
    "BENCHMARK_VERSION",
    "DATASET_VERSION",
    "DEFAULT_SYSTEMS",
    "BenchmarkResult",
    "DEFAULT_DATASET",
    "FailureRecord",
    "FilteredVectorRetriever",
    "MemoryTask",
    "QueryResult",
    "RunConfig",
    "TypedMemRetriever",
    "VectorRetriever",
    "build_history_record",
    "build_store",
    "category_improvement",
    "diagnose",
    "diagnose_all",
    "evaluate_query",
    "failure_summary",
    "is_failure",
    "load_tasks",
    "mean_metrics",
    "run_benchmark",
    "stage_contribution",
    "write_run_artifacts",
]
