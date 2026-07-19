# Memory Retrieval Benchmark — seed

- tasks: **33**  ·  k: **5**  ·  seed: **0**  ·  embedder: `hashing:dim=1024;ngram=2`  ·  typedmem: `0.8.0`

## Overall

| System | Recall@k | Prec@k | MRR | NDCG | Wrong-rate | Stale-rate | Cur-state |
|---|---|---|---|---|---|---|---|
| vector |   1.00 |   0.45 |   0.64 |   0.74 |   0.55 |   0.37 |   0.30 |
| vector_filter |   0.91 |   0.42 |   0.58 |   0.67 |   0.49 |   0.34 |   0.27 |
| typedmem |   0.91 |   0.73 |   0.88 |   0.89 |   0.18 |   0.00 |   0.85 |

> Wrong-rate and Stale-rate are lower-is-better; all others higher-is-better.

## Per category (Recall@k / Stale-rate / Cur-state)

| Category | vector | vector_filter | typedmem |
|---|---|---|---|
| contradictions | 1.00/0.50/0.00 | 1.00/0.50/0.00 | 1.00/0.00/1.00 |
| cross_session | 1.00/0.33/0.33 | 1.00/0.39/0.33 | 1.00/0.00/1.00 |
| decision_retrieval | 1.00/0.25/0.00 | 1.00/0.25/0.00 | 1.00/0.00/0.50 |
| entity_disambiguation | 1.00/0.00/1.00 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| goal_evolution | 1.00/0.54/0.50 | 0.75/0.42/0.25 | 0.75/0.00/0.75 |
| long_history_retrieval | 1.00/0.20/0.00 | 1.00/0.29/0.00 | 1.00/0.00/1.00 |
| preference_evolution | 1.00/0.50/0.75 | 1.00/0.50/0.75 | 1.00/0.00/1.00 |
| status_tracking | 1.00/0.50/0.00 | 0.50/0.25/0.00 | 0.50/0.00/0.50 |
| temporal_updates | 1.00/0.50/0.00 | 1.00/0.50/0.00 | 1.00/0.00/1.00 |

## Failure examples — `typedmem` (5 total)

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
