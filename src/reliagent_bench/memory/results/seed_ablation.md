# Memory Retrieval Benchmark — seed

- tasks: **42**  ·  k: **5**  ·  seed: **0**  ·  embedder: `hashing:dim=1024;ngram=2`  ·  typedmem: `0.8.0`

## Overall

| System | Recall@k | Prec@k | MRR | NDCG | Wrong-rate | Stale-rate | Cur-state |
|---|---|---|---|---|---|---|---|
| vector |   0.98 |   0.45 |   0.64 |   0.72 |   0.55 |   0.37 |   0.31 |
| +filters |   0.90 |   0.43 |   0.58 |   0.67 |   0.48 |   0.34 |   0.29 |
| +resolver |   0.90 |   0.74 |   0.85 |   0.86 |   0.17 |   0.00 |   0.81 |
| full |   0.90 |   0.74 |   0.88 |   0.89 |   0.17 |   0.00 |   0.86 |

> Wrong-rate and Stale-rate are lower-is-better; all others higher-is-better.

## Per category (Recall@k / Stale-rate / Cur-state)

| Category | vector | +filters | +resolver | full |
|---|---|---|---|---|
| contradictions | 1.00/0.50/0.00 | 1.00/0.50/0.00 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| cross_session | 1.00/0.33/0.25 | 1.00/0.42/0.25 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| decision_retrieval | 1.00/0.30/0.00 | 1.00/0.30/0.00 | 1.00/0.00/0.60 | 1.00/0.00/0.60 |
| entity_disambiguation | 1.00/0.07/1.00 | 1.00/0.07/1.00 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| goal_evolution | 1.00/0.53/0.40 | 0.80/0.43/0.20 | 0.80/0.00/0.80 | 0.80/0.00/0.80 |
| long_history_retrieval | 0.75/0.20/0.00 | 1.00/0.28/0.00 | 1.00/0.00/0.50 | 1.00/0.00/1.00 |
| preference_evolution | 1.00/0.50/0.80 | 1.00/0.50/0.80 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| status_tracking | 1.00/0.50/0.00 | 0.40/0.20/0.00 | 0.40/0.00/0.40 | 0.40/0.00/0.40 |
| temporal_updates | 1.00/0.40/0.20 | 1.00/0.40/0.20 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |

## Failure examples — `full` (6 total)

- **goal-03** (goal_evolution) — “What is the user currently saving money for?”
  - retrieved: `[]`  ·  cur-state=0  ·  stale-rate=0.00
- **dec-01** (decision_retrieval) — “Why did the user reject the Espresso Inc offer?”
  - retrieved: `['m1', 'm2']`  ·  cur-state=0  ·  stale-rate=0.00
- **dec-02** (decision_retrieval) — “Which database did the user decide to use?”
  - retrieved: `['m2', 'm1']`  ·  cur-state=0  ·  stale-rate=0.00
- **stat-03** (status_tracking) — “What is the current state of the bug ticket?”
  - retrieved: `[]`  ·  cur-state=0  ·  stale-rate=0.00
- **stat-04** (status_tracking) — “What is the current status of the gym membership?”
  - retrieved: `[]`  ·  cur-state=0  ·  stale-rate=0.00
- **stat-05** (status_tracking) — “What is the current status of the visa application?”
  - retrieved: `[]`  ·  cur-state=0  ·  stale-rate=0.00

## Analysis

### Category breakdown — current_state_accuracy (vector → full)

| Category | vector | full | Improvement |
|---|---|---|---|
| contradictions | 0.00 | 1.00 | +1.00 |
| cross_session | 0.25 | 1.00 | +0.75 |
| decision_retrieval | 0.00 | 0.60 | +0.60 |
| entity_disambiguation | 1.00 | 1.00 | +0.00 |
| goal_evolution | 0.40 | 0.80 | +0.40 |
| long_history_retrieval | 0.00 | 1.00 | +1.00 |
| preference_evolution | 0.80 | 1.00 | +0.20 |
| status_tracking | 0.00 | 0.40 | +0.40 |
| temporal_updates | 0.20 | 1.00 | +0.80 |

# Failure analysis — `full`

Total failures: **6**

| Failure type | Count |
|---|---:|
| router | 4 |
| entity | 0 |
| embedding | 0 |
| temporal | 0 |
| ranking | 2 |
| unknown | 0 |

### Stage contribution

| Stage | Failures |
|---|---:|
| router / typed filters | 4 |
| reranker | 2 |

### Cases

- **goal-03** (goal_evolution · medium) — “What is the user currently saving money for?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **dec-01** (decision_retrieval · medium) — “Why did the user reject the Espresso Inc offer?”
  - failure_type: `ranking`
  - expected: `['m2']` · retrieved: `['m1', 'm2']`
  - root_cause: the relevant memory survived to ranking but was ranked below the cutoff
  - possible_fix: tune the reranker (semantic/recency/type weights)
- **dec-02** (decision_retrieval · medium) — “Which database did the user decide to use?”
  - failure_type: `ranking`
  - expected: `['m1']` · retrieved: `['m2', 'm1']`
  - root_cause: the relevant memory survived to ranking but was ranked below the cutoff
  - possible_fix: tune the reranker (semantic/recency/type weights)
- **stat-03** (status_tracking · medium) — “What is the current state of the bug ticket?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **stat-04** (status_tracking · medium) — “What is the current status of the gym membership?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **stat-05** (status_tracking · medium) — “What is the current status of the visa application?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
