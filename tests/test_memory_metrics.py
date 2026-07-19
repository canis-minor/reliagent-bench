"""Metric correctness — hand-checked expected values."""

import math

from reliagent_bench.memory.metrics import (
    current_state_accuracy,
    entity_resolution_accuracy,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    stale_memory_rate,
    wrong_memory_rate,
)

RETRIEVED = ["a", "b", "c", "d"]
RELEVANT = {"b", "d"}
STALE = {"a"}


def test_recall_at_k():
    assert recall_at_k(RETRIEVED, RELEVANT, k=2) == 0.5   # only b in top-2
    assert recall_at_k(RETRIEVED, RELEVANT, k=4) == 1.0   # b and d
    assert recall_at_k(RETRIEVED, set(), k=4) == 1.0      # no relevant → vacuous 1.0


def test_precision_at_k():
    assert precision_at_k(RETRIEVED, RELEVANT, k=2) == 0.5   # b of {a,b}
    assert precision_at_k(RETRIEVED, RELEVANT, k=4) == 0.5   # b,d of 4
    assert precision_at_k([], RELEVANT, k=4) == 0.0


def test_mrr():
    assert mrr(RETRIEVED, RELEVANT) == 0.5                 # first hit at rank 2
    assert mrr(["b"], RELEVANT) == 1.0
    assert mrr(["x", "y"], RELEVANT) == 0.0


def test_ndcg_at_k():
    # Hits at ranks 2 and 4: DCG = 1/log2(3) + 1/log2(5)
    dcg = 1 / math.log2(3) + 1 / math.log2(5)
    # Ideal: two hits at ranks 1,2: 1/log2(2) + 1/log2(3)
    idcg = 1 / math.log2(2) + 1 / math.log2(3)
    assert math.isclose(ndcg_at_k(RETRIEVED, RELEVANT, k=4), dcg / idcg)
    # Perfect ordering → 1.0
    assert math.isclose(ndcg_at_k(["b", "d"], RELEVANT, k=2), 1.0)


def test_wrong_memory_rate():
    # top-4: a,c wrong → 2/4
    assert wrong_memory_rate(RETRIEVED, RELEVANT, k=4) == 0.5
    assert wrong_memory_rate(["b", "d"], RELEVANT, k=2) == 0.0


def test_stale_memory_rate():
    assert stale_memory_rate(RETRIEVED, STALE, k=4) == 0.25   # a of 4
    assert stale_memory_rate(["b", "d"], STALE, k=2) == 0.0
    assert stale_memory_rate(RETRIEVED, set(), k=4) == 0.0


def test_current_state_accuracy():
    assert current_state_accuracy(["b", "a"], RELEVANT) == 1.0   # top-1 relevant
    assert current_state_accuracy(["a", "b"], RELEVANT) == 0.0   # top-1 not relevant
    assert current_state_accuracy([], RELEVANT) == 0.0


def test_entity_resolution_accuracy():
    subjects = {"a": "apple_company", "b": "apple_fruit"}
    assert entity_resolution_accuracy(["a"], "apple_company", subjects) == 1.0
    assert entity_resolution_accuracy(["b"], "apple_company", subjects) == 0.0
    assert entity_resolution_accuracy([], "apple_company", subjects) == 0.0
