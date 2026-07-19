# Validation — does the routing conclusion hold at scale?

- dataset **1.0** · **104** tasks · held-out eval **32** · benchmark **1.0**
- No TypedMem / router / retrieval changes — measurement only.

### Oracle Gap (Oracle − variant, held-out eval; lower = closer to ideal)

| Variant | current state accuracy | recall at k | precision at k |
|---|---|---|---|
| A_rule_hard | +0.19 | +0.19 | +0.22 |
| B_none | +0.00 | +0.00 | +0.07 |
| C_soft_top2 | +0.19 | +0.19 | +0.22 |
| D_rule_fallback | +0.00 | +0.00 | +0.07 |

### Failure distribution — typedmem (24 failures over 104 tasks)

| Failure type | Count | Percentage |
|---|---:|---:|
| router | 21 | 88% |
| entity | 1 | 4% |
| embedding | 0 | 0% |
| temporal | 0 | 0% |
| ranking | 2 | 8% |
| unknown | 0 | 0% |

### Stability across benchmark versions (typedmem)

| bench / dataset | tasks | Recall | Cur-state | Stale | Router-fail % |
|---|---:|---:|---:|---:|---:|
| 1.1 / 0.2 | 42 | 0.90 | 0.86 | 0.00 | 67% |
| 1.3 / 0.3 | 82 | 0.83 | 0.79 | 0.00 | 82% |
| 1.0 / 1.0 | 104 | 0.79 | 0.77 | 0.00 | 88% |

## Decision

**Case A.** Rule+Fallback current-state gap to Oracle is +0.00 (<= 0.05); freeze routing, move to external baselines

→ Rule+Fallback ≈ Oracle → **freeze routing; move to external baselines (Mem0/LangMem/Zep).**