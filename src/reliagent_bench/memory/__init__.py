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
from .router_experiment import (
    default_variants,
    router_failure_subtype,
    router_metrics,
    run_router_matrix,
    split_tasks,
)
from .router_pipeline import RouterPipelineRetriever
from .routers import (
    HybridRouter,
    LLMRouter,
    NoRouter,
    OracleRouter,
    RouteResult,
    RuleRouter,
    SoftRuleRouter,
)
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
    "HybridRouter",
    "LLMRouter",
    "MemoryTask",
    "NoRouter",
    "OracleRouter",
    "QueryResult",
    "RouteResult",
    "RouterPipelineRetriever",
    "RuleRouter",
    "RunConfig",
    "SoftRuleRouter",
    "TypedMemRetriever",
    "VectorRetriever",
    "build_history_record",
    "build_store",
    "category_improvement",
    "default_variants",
    "diagnose",
    "diagnose_all",
    "evaluate_query",
    "failure_summary",
    "is_failure",
    "load_tasks",
    "mean_metrics",
    "router_failure_subtype",
    "router_metrics",
    "run_benchmark",
    "run_router_matrix",
    "split_tasks",
    "stage_contribution",
    "write_run_artifacts",
]
