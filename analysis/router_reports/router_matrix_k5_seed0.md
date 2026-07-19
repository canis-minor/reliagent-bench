# Router experiment — benchmark matrix

- dev tasks: **56** · eval (held-out) tasks: **26** · k=5 · seed=0
- Only routing varies; resolver + ranker fixed. Higher is better except Stale / ExclRate / EmptyRate.
- Variants E (LLM) and F (Hybrid) require an LLM client/cache and are not in this offline run.

### Held-out evaluation set (the honest comparison)

| Variant | Recall | Prec | Cur-state | Stale | AccTypeRecall | ExclRate | EmptyRate | AvgTypes |
|---|---|---|---|---|---|---|---|---|
| A_rule_hard | 0.85 | 0.71 | 0.81 | 0.00 | 0.85 | 0.15 | 0.15 | 0.77 |
| B_none | 1.00 | 0.84 | 0.96 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| C_soft_top2 | 0.85 | 0.71 | 0.81 | 0.00 | 0.85 | 0.15 | 0.15 | 0.77 |
| D_rule_fallback | 1.00 | 0.84 | 0.96 | 0.00 | 0.85 | 0.15 | 0.00 | 0.77 |
| Oracle_ceiling | 1.00 | 0.90 | 0.96 | 0.00 | 1.00 | 0.00 | 0.00 | 1.04 |

Router-failure subtypes:

| Variant | overly_narrow | wrong_type | no_route | correct_route_empty | ambiguous |
|---|---|---|---|---|---|
| A_rule_hard | 4 | 0 | 0 | 0 | 1 |
| B_none | 0 | 0 | 1 | 0 | 0 |
| C_soft_top2 | 4 | 0 | 0 | 0 | 1 |
| D_rule_fallback | 0 | 0 | 0 | 0 | 1 |
| Oracle_ceiling | 0 | 0 | 0 | 0 | 1 |

### Development set

| Variant | Recall | Prec | Cur-state | Stale | AccTypeRecall | ExclRate | EmptyRate | AvgTypes |
|---|---|---|---|---|---|---|---|---|
| A_rule_hard | 0.82 | 0.66 | 0.79 | 0.00 | 0.82 | 0.18 | 0.18 | 0.96 |
| B_none | 1.00 | 0.80 | 0.96 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| C_soft_top2 | 0.82 | 0.66 | 0.79 | 0.00 | 0.82 | 0.18 | 0.18 | 0.96 |
| D_rule_fallback | 1.00 | 0.80 | 0.96 | 0.00 | 0.82 | 0.18 | 0.00 | 0.96 |
| Oracle_ceiling | 1.00 | 0.88 | 0.96 | 0.00 | 1.00 | 0.00 | 0.00 | 1.02 |

Router-failure subtypes:

| Variant | overly_narrow | wrong_type | no_route | correct_route_empty | ambiguous |
|---|---|---|---|---|---|
| A_rule_hard | 10 | 0 | 0 | 0 | 2 |
| B_none | 0 | 0 | 2 | 0 | 0 |
| C_soft_top2 | 10 | 0 | 0 | 0 | 2 |
| D_rule_fallback | 0 | 0 | 0 | 0 | 2 |
| Oracle_ceiling | 0 | 0 | 0 | 0 | 2 |

> `Oracle_ceiling` routes each query to its labeled type — an upper bound for what perfect routing could achieve, not a deployable router.