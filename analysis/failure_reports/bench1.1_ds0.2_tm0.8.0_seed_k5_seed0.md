# Failure analysis — `typedmem`

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