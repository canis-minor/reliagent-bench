# Metrics (ReliAgent Bench v1.0)

Let `R` be the ranked list of retrieved memory ids (truncated to top-`k`), `Rel`
the set of relevant (current) ids, and `Stale` the set of stale (superseded) ids
for a task. `1[·]` is the indicator function.

## Retrieval metrics

**Recall@K** — fraction of relevant memories present in the top-k:

```
Recall@K = |{top-k} ∩ Rel| / |Rel|      (1.0 if Rel is empty)
```

**Precision@K** — fraction of the top-k that are relevant:

```
Precision@K = |{top-k} ∩ Rel| / |top-k|   (0.0 if nothing retrieved)
```

**MRR** — reciprocal rank of the first relevant hit:

```
MRR = 1 / rank_of_first_relevant      (0 if none in top-k)
```

**NDCG@K** — binary-relevance normalized discounted cumulative gain:

```
DCG@K  = Σ_{i=1..k}  1[R_i ∈ Rel] / log2(i + 1)
IDCG@K = Σ_{i=1..min(|Rel|,k)}  1 / log2(i + 1)
NDCG@K = DCG@K / IDCG@K                (0 if IDCG = 0)
```

## Memory-specific metrics

**Current-State Accuracy** — is the top-ranked memory a current one? (per task,
averaged):

```
CurrentState = 1[ R_1 ∈ Rel ]
```

**Wrong-Memory Rate** — fraction of the top-k that are *not* relevant (= 1 −
Precision@K):

```
WrongRate = |{top-k} \ Rel| / |top-k|
```

**Stale-Memory Rate** — fraction of the top-k that are explicitly stale:

```
StaleRate = |{top-k} ∩ Stale| / |top-k|
```

## Router-study metrics

**Oracle Gap** — for any metric `M`, the shortfall of a variant vs. the Oracle
router (which routes to the labeled types):

```
OracleGap_M(variant) = M(Oracle) − M(variant)
```

A gap of ~0 on Current-State Accuracy means routing is effectively solved.

**Exact type accuracy** — `1[ predicted_types == relevant_types ]`.
**Acceptable type recall** — `1[ relevant_types ⊆ predicted_types  or  predicted_types = ∅ ]`.
**Candidate exclusion rate** — `1[ predicted_types ≠ ∅ and relevant_types ⊄ predicted_types ]`.
**Empty-result / fallback rate** — fraction of tasks with an empty filtered
result / with the global fallback activated.

## Aggregation

All metrics are computed per task and averaged (macro). Category and difficulty
breakdowns average within the group. Metrics that do not apply to a task (e.g.
entity-resolution on a non-entity task) are omitted from that task's mean rather
than counted as zero.
