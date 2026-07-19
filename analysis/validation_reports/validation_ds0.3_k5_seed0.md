# Validation — does the routing conclusion hold at scale?

- dataset **0.3** · **82** tasks · held-out eval **26** · benchmark **1.3**
- No TypedMem / router / retrieval changes — measurement only.

### Oracle Gap (Oracle − variant, held-out eval; lower = closer to ideal)

| Variant | current state accuracy | recall at k | precision at k |
|---|---|---|---|
| A_rule_hard | +0.15 | +0.15 | +0.18 |
| B_none | +0.00 | +0.00 | +0.06 |
| C_soft_top2 | +0.15 | +0.15 | +0.18 |
| D_rule_fallback | +0.00 | +0.00 | +0.06 |

### Failure distribution — typedmem (17 failures over 82 tasks)

| Failure type | Count | Percentage |
|---|---:|---:|
| router | 14 | 82% |
| entity | 1 | 6% |
| embedding | 0 | 0% |
| temporal | 0 | 0% |
| ranking | 2 | 12% |
| unknown | 0 | 0% |

### Stability across benchmark versions (typedmem)

| bench / dataset | tasks | Recall | Cur-state | Stale | Router-fail % |
|---|---:|---:|---:|---:|---:|
| 1.1 / 0.2 | 42 | 0.90 | 0.86 | 0.00 | 67% |
| 1.3 / 0.3 | 82 | 0.83 | 0.79 | 0.00 | 82% |

## Decision

**Case A.** Rule+Fallback current-state gap to Oracle is +0.00 (<= 0.05); freeze routing, move to external baselines

→ Rule+Fallback ≈ Oracle → **freeze routing; move to external baselines (Mem0/LangMem/Zep).**