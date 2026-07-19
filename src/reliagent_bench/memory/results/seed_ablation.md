# Memory Retrieval Benchmark — seed

- tasks: **18**  ·  k: **5**  ·  seed: **0**  ·  embedder: `hashing:dim=1024;ngram=2`  ·  typedmem: `0.8.0`

## Overall

| System | Recall@k | Prec@k | MRR | NDCG | Wrong-rate | Stale-rate | Cur-state |
|---|---|---|---|---|---|---|---|
| vector |   1.00 |   0.49 |   0.67 |   0.75 |   0.51 |   0.37 |   0.33 |
| +filters |   0.89 |   0.44 |   0.58 |   0.66 |   0.45 |   0.31 |   0.28 |
| +resolver |   0.89 |   0.75 |   0.83 |   0.85 |   0.14 |   0.00 |   0.78 |
| full |   0.89 |   0.75 |   0.83 |   0.85 |   0.14 |   0.00 |   0.78 |

> Wrong-rate and Stale-rate are lower-is-better; all others higher-is-better.

## Per category (Recall@k / Stale-rate / Cur-state)

| Category | vector | +filters | +resolver | full |
|---|---|---|---|---|
| decision_retrieval | 1.00/0.17/0.00 | 1.00/0.17/0.00 | 1.00/0.00/0.33 | 1.00/0.00/0.33 |
| entity_disambiguation | 1.00/0.00/1.00 | 1.00/0.00/1.00 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| goal_evolution | 1.00/0.56/0.33 | 0.67/0.39/0.00 | 0.67/0.00/0.67 | 0.67/0.00/0.67 |
| preference_evolution | 1.00/0.50/0.67 | 1.00/0.50/0.67 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| status_tracking | 1.00/0.50/0.00 | 0.67/0.33/0.00 | 0.67/0.00/0.67 | 0.67/0.00/0.67 |
| temporal_updates | 1.00/0.50/0.00 | 1.00/0.50/0.00 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |

## Failure examples — `full` (4 total)

- **goal-03** (goal_evolution) — “What is the user currently saving money for?”
  - retrieved: `[]`  ·  cur-state=0  ·  stale-rate=0.00
- **dec-01** (decision_retrieval) — “Why did the user reject the Espresso Inc offer?”
  - retrieved: `['m1', 'm2']`  ·  cur-state=0  ·  stale-rate=0.00
- **dec-02** (decision_retrieval) — “Which database did the user decide to use?”
  - retrieved: `['m2', 'm1']`  ·  cur-state=0  ·  stale-rate=0.00
- **stat-03** (status_tracking) — “What is the current state of the bug ticket?”
  - retrieved: `[]`  ·  cur-state=0  ·  stale-rate=0.00
