"""Retrieval metrics — pure functions over ranked id lists.

Every function takes a ranked ``retrieved`` list of memory ids and a set of
``relevant`` ids (and, where relevant, ``stale`` ids). ``k`` truncates the ranked
list. These are deliberately simple and standard so the numbers are auditable.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def _top_k(retrieved: Sequence[str], k: int) -> list[str]:
    return list(retrieved[:k])


def recall_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    """Fraction of relevant memories present in the top-k."""
    if not relevant:
        return 1.0
    hit = set(_top_k(retrieved, k)) & relevant
    return len(hit) / len(relevant)


def precision_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    """Fraction of top-k that are relevant."""
    top = _top_k(retrieved, k)
    if not top:
        return 0.0
    return sum(1 for x in top if x in relevant) / len(top)


def mrr(retrieved: Sequence[str], relevant: set[str], k: int | None = None) -> float:
    """Reciprocal rank of the first relevant hit (0 if none in top-k)."""
    top = _top_k(retrieved, k) if k is not None else list(retrieved)
    for rank, x in enumerate(top, start=1):
        if x in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    """Binary-relevance NDCG@k (gain 1 per relevant hit, discount log2(rank+1))."""
    top = _top_k(retrieved, k)
    dcg = sum(1.0 / math.log2(rank + 1) for rank, x in enumerate(top, start=1) if x in relevant)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg > 0 else 0.0


def wrong_memory_rate(retrieved: Sequence[str], relevant: set[str], k: int) -> float:
    """Fraction of top-k that are NOT relevant (1 - precision@k)."""
    top = _top_k(retrieved, k)
    if not top:
        return 0.0
    return sum(1 for x in top if x not in relevant) / len(top)


def stale_memory_rate(retrieved: Sequence[str], stale: set[str], k: int) -> float:
    """Fraction of top-k that are explicitly stale (superseded / out-of-date)."""
    top = _top_k(retrieved, k)
    if not top:
        return 0.0
    return sum(1 for x in top if x in stale) / len(top)


def current_state_accuracy(retrieved: Sequence[str], relevant: set[str]) -> float:
    """1.0 if the top-ranked memory is a current (relevant) one, else 0.0."""
    top = _top_k(retrieved, 1)
    return 1.0 if top and top[0] in relevant else 0.0


def entity_resolution_accuracy(
    retrieved: Sequence[str],
    expected_entity: str,
    subject_of: dict[str, str | None],
) -> float:
    """1.0 if the top-ranked memory belongs to the expected entity, else 0.0."""
    top = _top_k(retrieved, 1)
    return 1.0 if top and subject_of.get(top[0]) == expected_entity else 0.0
