# Benchmark audit (Stage 0)

- tasks: **104**

## Fairness invariants

| Invariant | Held |
|---|---|
| same dataset | ✅ |
| same query per system | ✅ |
| same embedder | ✅ |
| same top k | ✅ |
| same evaluator | ✅ |
| deterministic | ✅ |

## Generality

- **Type leakage:** 19/104 (18%) queries literally name the answer's memory type (e.g. a goal task asking "...current goal?"). This is a natural phrasing and identical for every system, so it does not favor typed systems per se — but it is surfaced so reviewers can judge task difficulty. Ids: dec-02, dec-10, goal-01, goal-02, goal-04, goal-05, goal-07, mixed-01, mixed-02, mixed-04, pref-01, pref-02, pref-03, pref-04, pref-05, pref-06, pref-08, pref-10, xsess-10
- **Natural queries:** 104/104 are phrased as questions; non-question ids: none.

## Reproducibility

- one-command deterministic run (`--validate`, pure-hash embedder, fixed seed)
- committed expected outputs (`results/`, `analysis/`), frozen dataset manifest
- simple `retrieve(query, top_k) -> [memory_id]` adapter interface

**Verdict:** the benchmark is defendable for external comparison — fairness invariants hold, queries are natural, and every system is evaluated under identical conditions.
