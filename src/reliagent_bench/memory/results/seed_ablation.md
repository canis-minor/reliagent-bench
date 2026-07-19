# Memory Retrieval Benchmark — seed

- tasks: **104**  ·  k: **5**  ·  seed: **0**  ·  embedder: `hashing:dim=1024;ngram=2`  ·  typedmem: `0.8.0`

## Overall

| System | Recall@k | Prec@k | MRR | NDCG | Wrong-rate | Stale-rate | Cur-state |
|---|---|---|---|---|---|---|---|
| vector |   0.99 |   0.48 |   0.68 |   0.76 |   0.52 |   0.36 |   0.38 |
| +filters |   0.79 |   0.40 |   0.55 |   0.61 |   0.40 |   0.28 |   0.32 |
| +resolver |   0.79 |   0.66 |   0.76 |   0.76 |   0.14 |   0.00 |   0.74 |
| full |   0.79 |   0.66 |   0.78 |   0.78 |   0.14 |   0.00 |   0.77 |

> Wrong-rate and Stale-rate are lower-is-better; all others higher-is-better.

## Per category (Recall@k / Stale-rate / Cur-state)

| Category | vector | +filters | +resolver | full |
|---|---|---|---|---|
| contradictions | 1.00/0.50/0.00 | 1.00/0.50/0.00 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| cross_session | 1.00/0.33/0.40 | 1.00/0.42/0.40 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| decision_retrieval | 1.00/0.42/0.25 | 0.83/0.33/0.17 | 0.83/0.00/0.67 | 0.83/0.00/0.67 |
| entity_disambiguation | 1.00/0.03/0.92 | 1.00/0.03/0.92 | 1.00/0.00/0.92 | 1.00/0.00/0.92 |
| goal_evolution | 1.00/0.52/0.30 | 0.60/0.32/0.10 | 0.60/0.00/0.60 | 0.60/0.00/0.60 |
| implicit_decision | 1.00/0.50/1.00 | 0.00/0.00/0.00 | 0.00/0.00/0.00 | 0.00/0.00/0.00 |
| implicit_goal | 1.00/0.50/0.25 | 0.25/0.12/0.25 | 0.25/0.00/0.25 | 0.25/0.00/0.25 |
| long_history_retrieval | 0.90/0.20/0.00 | 1.00/0.32/0.00 | 1.00/0.00/0.70 | 1.00/0.00/1.00 |
| mixed_type | 1.00/0.00/1.00 | 0.80/0.00/1.00 | 0.80/0.00/1.00 | 0.80/0.00/1.00 |
| preference_evolution | 1.00/0.50/0.64 | 1.00/0.50/0.64 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |
| status_tracking | 1.00/0.50/0.09 | 0.18/0.09/0.00 | 0.18/0.00/0.18 | 0.18/0.00/0.18 |
| temporal_updates | 1.00/0.44/0.22 | 1.00/0.44/0.22 | 1.00/0.00/1.00 | 1.00/0.00/1.00 |

## Failure examples — `full` (24 total)

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
- … and 16 more

## Analysis

### Category breakdown — current_state_accuracy (vector → full)

| Category | vector | full | Improvement |
|---|---|---|---|
| contradictions | 0.00 | 1.00 | +1.00 |
| cross_session | 0.40 | 1.00 | +0.60 |
| decision_retrieval | 0.25 | 0.67 | +0.42 |
| entity_disambiguation | 0.92 | 0.92 | +0.00 |
| goal_evolution | 0.30 | 0.60 | +0.30 |
| implicit_decision | 1.00 | 0.00 | -1.00 |
| implicit_goal | 0.25 | 0.25 | +0.00 |
| long_history_retrieval | 0.00 | 1.00 | +1.00 |
| mixed_type | 1.00 | 1.00 | +0.00 |
| preference_evolution | 0.64 | 1.00 | +0.36 |
| status_tracking | 0.09 | 0.18 | +0.09 |
| temporal_updates | 0.22 | 1.00 | +0.78 |

# Failure analysis — `full`

Total failures: **24**

| Failure type | Count |
|---|---:|
| router | 21 |
| entity | 1 |
| embedding | 0 |
| temporal | 0 |
| ranking | 2 |
| unknown | 0 |

### Stage contribution

| Stage | Failures |
|---|---:|
| router / typed filters | 21 |
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
- **stat-10** (status_tracking · medium) — “What is the current status of the contract?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **stat-11** (status_tracking · medium) — “What is the current status of the refund request?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **implgoal-03** (implicit_goal · hard) — “What is the user's main health focus right now?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **implgoal-04** (implicit_goal · hard) — “What is the user prioritizing financially this year?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'goal' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **impldec-01** (implicit_decision · hard) — “What is the user's approach to state management now?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'decision' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **impldec-02** (implicit_decision · hard) — “What is the team's current deployment strategy?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'decision' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
- **impldec-03** (implicit_decision · hard) — “What is the user's stance on the pricing model?”
  - failure_type: `router`
  - expected: `['m2']` · retrieved: `[]`
  - root_cause: router predicted types ['fact']; the type filter dropped the relevant 'decision' memory
  - possible_fix: improve query routing (do not over-filter to a single type)
