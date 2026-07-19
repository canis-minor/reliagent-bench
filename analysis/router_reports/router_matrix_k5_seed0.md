# Router experiment — benchmark matrix

- dev tasks: **72** · eval (held-out) tasks: **32** · k=5 · seed=0
- Only routing varies; resolver + ranker fixed. Higher is better except Stale / ExclRate / EmptyRate.
- Variants E (LLM) and F (Hybrid) require an LLM client/cache and are not in this offline run.

### Held-out evaluation set (the honest comparison)

| Variant | Recall | Prec | Cur-state | Stale | AccTypeRecall | ExclRate | EmptyRate | AvgTypes |
|---|---|---|---|---|---|---|---|---|
| A_rule_hard | 0.81 | 0.67 | 0.78 | 0.00 | 0.81 | 0.19 | 0.19 | 0.81 |
| B_none | 1.00 | 0.82 | 0.97 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| C_soft_top2 | 0.81 | 0.67 | 0.78 | 0.00 | 0.81 | 0.19 | 0.19 | 0.81 |
| D_rule_fallback | 1.00 | 0.82 | 0.97 | 0.00 | 0.81 | 0.19 | 0.00 | 0.81 |
| Oracle_ceiling | 1.00 | 0.89 | 0.97 | 0.00 | 1.00 | 0.00 | 0.00 | 1.06 |

Router-failure subtypes:

| Variant | overly_narrow | wrong_type | no_route | correct_route_empty | ambiguous |
|---|---|---|---|---|---|
| A_rule_hard | 6 | 0 | 0 | 0 | 1 |
| B_none | 0 | 0 | 1 | 0 | 0 |
| C_soft_top2 | 6 | 0 | 0 | 0 | 1 |
| D_rule_fallback | 0 | 0 | 0 | 0 | 1 |
| Oracle_ceiling | 0 | 0 | 0 | 0 | 1 |

### Development set

| Variant | Recall | Prec | Cur-state | Stale | AccTypeRecall | ExclRate | EmptyRate | AvgTypes |
|---|---|---|---|---|---|---|---|---|
| A_rule_hard | 0.78 | 0.65 | 0.76 | 0.00 | 0.76 | 0.24 | 0.21 | 0.94 |
| B_none | 1.00 | 0.81 | 0.97 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| C_soft_top2 | 0.78 | 0.65 | 0.76 | 0.00 | 0.76 | 0.24 | 0.21 | 0.94 |
| D_rule_fallback | 1.00 | 0.81 | 0.97 | 0.00 | 0.76 | 0.24 | 0.00 | 0.94 |
| Oracle_ceiling | 1.00 | 0.89 | 0.97 | 0.00 | 1.00 | 0.00 | 0.00 | 1.04 |

Router-failure subtypes:

| Variant | overly_narrow | wrong_type | no_route | correct_route_empty | ambiguous |
|---|---|---|---|---|---|
| A_rule_hard | 15 | 0 | 0 | 0 | 2 |
| B_none | 0 | 0 | 2 | 0 | 0 |
| C_soft_top2 | 15 | 0 | 0 | 0 | 2 |
| D_rule_fallback | 0 | 0 | 0 | 0 | 2 |
| Oracle_ceiling | 0 | 0 | 0 | 0 | 2 |

> `Oracle_ceiling` routes each query to its labeled type — an upper bound for what perfect routing could achieve, not a deployable router.