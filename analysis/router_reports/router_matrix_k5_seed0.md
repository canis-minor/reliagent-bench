# Router experiment — benchmark matrix

- dev tasks: **27** · eval (held-out) tasks: **15** · k=5 · seed=0
- Only routing varies; resolver + ranker fixed. Higher is better except Stale / ExclRate / EmptyRate.
- Variants E (LLM) and F (Hybrid) require an LLM client/cache and are not in this offline run.

### Held-out evaluation set (the honest comparison)

| Variant | Recall | Prec | Cur-state | Stale | AccTypeRecall | ExclRate | EmptyRate | AvgTypes |
|---|---|---|---|---|---|---|---|---|
| A_rule_hard | 0.93 | 0.77 | 0.87 | 0.00 | 0.93 | 0.07 | 0.07 | 0.93 |
| B_none | 1.00 | 0.81 | 0.93 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| C_soft_top2 | 0.93 | 0.77 | 0.87 | 0.00 | 0.93 | 0.07 | 0.07 | 0.93 |
| D_rule_fallback | 1.00 | 0.81 | 0.93 | 0.00 | 0.93 | 0.07 | 0.00 | 0.93 |
| Oracle_ceiling | 1.00 | 0.87 | 0.93 | 0.00 | 1.00 | 0.00 | 0.00 | 1.00 |

Router-failure subtypes:

| Variant | overly_narrow | wrong_type | no_route | correct_route_empty | ambiguous |
|---|---|---|---|---|---|
| A_rule_hard | 1 | 0 | 0 | 0 | 1 |
| B_none | 0 | 0 | 1 | 0 | 0 |
| C_soft_top2 | 1 | 0 | 0 | 0 | 1 |
| D_rule_fallback | 0 | 0 | 0 | 0 | 1 |
| Oracle_ceiling | 0 | 0 | 0 | 0 | 1 |

### Development set

| Variant | Recall | Prec | Cur-state | Stale | AccTypeRecall | ExclRate | EmptyRate | AvgTypes |
|---|---|---|---|---|---|---|---|---|
| A_rule_hard | 0.89 | 0.72 | 0.85 | 0.00 | 0.89 | 0.11 | 0.11 | 0.89 |
| B_none | 1.00 | 0.78 | 0.96 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| C_soft_top2 | 0.89 | 0.72 | 0.85 | 0.00 | 0.89 | 0.11 | 0.11 | 0.89 |
| D_rule_fallback | 1.00 | 0.78 | 0.96 | 0.00 | 0.89 | 0.11 | 0.00 | 0.89 |
| Oracle_ceiling | 1.00 | 0.86 | 0.96 | 0.00 | 1.00 | 0.00 | 0.00 | 1.00 |

Router-failure subtypes:

| Variant | overly_narrow | wrong_type | no_route | correct_route_empty | ambiguous |
|---|---|---|---|---|---|
| A_rule_hard | 3 | 0 | 0 | 0 | 1 |
| B_none | 0 | 0 | 1 | 0 | 0 |
| C_soft_top2 | 3 | 0 | 0 | 0 | 1 |
| D_rule_fallback | 0 | 0 | 0 | 0 | 1 |
| Oracle_ceiling | 0 | 0 | 0 | 0 | 1 |

> `Oracle_ceiling` routes each query to its labeled type — an upper bound for what perfect routing could achieve, not a deployable router.