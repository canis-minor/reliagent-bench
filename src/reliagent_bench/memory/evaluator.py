"""Per-query evaluation + aggregation.

``evaluate_query`` scores one (task, retrieved) pair into a metric dict; the
aggregation helpers average metric dicts across queries — overall and grouped by
category. ``entity_resolution`` is only defined for entity-disambiguation tasks
(those carrying ``expected_entity``); it is left out of the dict otherwise and
skipped in the mean, so it never dilutes the other categories.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from . import metrics as M
from .dataset import MemoryTask, subject_map

# Metric keys reported per query (entity_resolution added conditionally).
METRIC_KEYS = [
    "recall_at_k",
    "precision_at_k",
    "mrr",
    "ndcg_at_k",
    "wrong_memory_rate",
    "stale_memory_rate",
    "current_state_accuracy",
]


def evaluate_query(
    task: MemoryTask,
    retrieved: Sequence[str],
    k: int,
    subjects: dict[str, str | None] | None = None,
) -> dict[str, float]:
    relevant, stale = task.relevant, task.stale
    result = {
        "recall_at_k": M.recall_at_k(retrieved, relevant, k),
        "precision_at_k": M.precision_at_k(retrieved, relevant, k),
        "mrr": M.mrr(retrieved, relevant, k),
        "ndcg_at_k": M.ndcg_at_k(retrieved, relevant, k),
        "wrong_memory_rate": M.wrong_memory_rate(retrieved, relevant, k),
        "stale_memory_rate": M.stale_memory_rate(retrieved, stale, k),
        "current_state_accuracy": M.current_state_accuracy(retrieved, relevant),
    }
    if task.expected_entity is not None:
        subjects = subjects if subjects is not None else subject_map(task)
        result["entity_resolution"] = M.entity_resolution_accuracy(
            retrieved, task.expected_entity, subjects,
        )
    return result


def mean_metrics(metric_dicts: Sequence[dict[str, float]]) -> dict[str, float]:
    """Average each metric across dicts, skipping keys that are absent (e.g.
    entity_resolution outside entity tasks)."""
    sums: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for d in metric_dicts:
        for key, value in d.items():
            sums[key] += value
            counts[key] += 1
    return {key: sums[key] / counts[key] for key in sums}
