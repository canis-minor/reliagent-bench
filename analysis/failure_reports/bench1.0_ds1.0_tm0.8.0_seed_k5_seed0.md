# Failure analysis — `typedmem`

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