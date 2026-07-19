# Memory Retrieval Benchmark — seed

- tasks: **82**  ·  k: **5**  ·  seed: **0**  ·  embedder: `hashing:dim=1024;ngram=2`  ·  typedmem: `0.8.0`

## Overall

| System | Recall@k | Prec@k | MRR | NDCG | Wrong-rate | Stale-rate | Cur-state |
|---|---|---|---|---|---|---|---|
| vector |   0.99 |   0.47 |   0.66 |   0.75 |   0.53 |   0.37 |   0.35 |
| vector_filter |   0.83 |   0.40 |   0.56 |   0.63 |   0.43 |   0.30 |   0.30 |
| typedmem |   0.83 |   0.67 |   0.81 |   0.82 |   0.16 |   0.00 |   0.79 |

> Wrong-rate and Stale-rate are lower-is-better; all others higher-is-better.

## Per category (Recall@k / Stale-rate / Cur-state)

| Category | vector | vector_filter | typedmem |
|---|---|---|---|
| contradictions | 1.00/0.50/0.00 | 1.00/0.50/0.00 | 1.00/0.00/1.00 |
| cross_session | 1.00/0.33/0.29 | 1.00/0.38/0.29 | 1.00/0.00/1.00 |
| decision_retrieval | 1.00/0.40/0.30 | 0.80/0.30/0.20 | 0.80/0.00/0.60 |
| entity_disambiguation | 1.00/0.03/0.90 | 1.00/0.03/0.90 | 1.00/0.00/0.90 |
| goal_evolution | 1.00/0.52/0.30 | 0.60/0.32/0.10 | 0.60/0.00/0.60 |
| implicit_goal | 1.00/0.50/0.50 | 0.50/0.25/0.50 | 0.50/0.00/0.50 |
| long_history_retrieval | 0.86/0.20/0.00 | 1.00/0.28/0.00 | 1.00/0.00/1.00 |
| mixed_type | 1.00/0.00/1.00 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| preference_evolution | 1.00/0.50/0.67 | 1.00/0.50/0.67 | 1.00/0.00/1.00 |
| status_tracking | 1.00/0.50/0.11 | 0.22/0.11/0.00 | 0.22/0.00/0.22 |
| temporal_updates | 1.00/0.44/0.22 | 1.00/0.44/0.22 | 1.00/0.00/1.00 |

## Failure examples — `typedmem` (17 total)

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
- **goal-06** (goal_evolution) — “What is the user focused on achieving this quarter?”
  - retrieved: `[]`  ·  cur-state=0  ·  stale-rate=0.00
- **goal-08** (goal_evolution) — “What is the user saving toward right now?”
  - retrieved: `[]`  ·  cur-state=0  ·  stale-rate=0.00
- … and 9 more

## Analysis

### Category breakdown — current_state_accuracy (vector → typedmem)

| Category | vector | typedmem | Improvement |
|---|---|---|---|
| contradictions | 0.00 | 1.00 | +1.00 |
| cross_session | 0.29 | 1.00 | +0.71 |
| decision_retrieval | 0.30 | 0.60 | +0.30 |
| entity_disambiguation | 0.90 | 0.90 | +0.00 |
| goal_evolution | 0.30 | 0.60 | +0.30 |
| implicit_goal | 0.50 | 0.50 | +0.00 |
| long_history_retrieval | 0.00 | 1.00 | +1.00 |
| mixed_type | 1.00 | 1.00 | +0.00 |
| preference_evolution | 0.67 | 1.00 | +0.33 |
| status_tracking | 0.11 | 0.22 | +0.11 |
| temporal_updates | 0.22 | 1.00 | +0.78 |

# Failure analysis — `typedmem`

Total failures: **17**

| Failure type | Count |
|---|---:|
| router | 14 |
| entity | 1 |
| embedding | 0 |
| temporal | 0 |
| ranking | 2 |
| unknown | 0 |

### Stage contribution

| Stage | Failures |
|---|---:|
| router / typed filters | 14 |
| reranker | 2 |
| router / entity resolution | 1 |

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
- **goal-06** (goal_evolution · medium) — “What is the user focused on achieving this quarter?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **goal-08** (goal_evolution · medium) — “What is the user saving toward right now?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **goal-10** (goal_evolution · medium) — “What is the user hoping to accomplish at work this year?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **dec-06** (decision_retrieval · medium) — “What is the user's final choice of CI system?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'decision' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **dec-08** (decision_retrieval · medium) — “What license did the user settle on for the project?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['goal']; the type filter dropped the relevant 'decision' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **ent-10** (entity_disambiguation · medium) — “What is Mercury the car brand known for?”
  - failure_type: `entity`
  - expected: `['m1']` · retrieved: `['m2', 'm1']`
  - root_cause: top result belongs to the wrong entity (expected 'mercury_carbrand')
  - possible_fix: add entity resolution to routing/filters
- **stat-06** (status_tracking · medium) — “What is the current status of the online order?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **stat-07** (status_tracking · medium) — “What is the current status of the pull request?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **stat-08** (status_tracking · medium) — “What is the current status of the loan application?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **stat-09** (status_tracking · medium) — “What is the current status of the server migration?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **implgoal-01** (implicit_goal · hard) — “What is the user working toward with their savings?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)

_analysis written under /Users/ruxiz/projects/reliagent-bench/analysis/ (record: bench1.3_ds0.3_tm0.8.0_seed_k5_seed0.json)_
