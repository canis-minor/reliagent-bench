# Analysis

Versioned benchmark history and failure analysis — the artifacts that make the
benchmark, not intuition, the source of engineering decisions.

```text
analysis/
    benchmark_history/   run records: benchmark/dataset/typedmem versions,
                         commit hashes, config, seed, overall metrics, failures
    category_reports/    per-category baseline→target improvement tables
    failure_reports/     every target-system failure, classified with a fix
    router_reports/      router experiment matrix (variants A-F + Oracle)
    validation_reports/  Oracle gap + failure distribution + stability + decision
    plots/               (reserved)
```

Regenerate (writes a record keyed by version + config; new versions are kept,
same config overwrites its own record):

```bash
python -m reliagent_bench.memory --k 5 --seed 0 --save-analysis
```

## Failure taxonomy

Each failure of the target system is traced through the public TypedMem stages
and labeled: `router` (type filter dropped the relevant memory), `embedding`
(never a vector candidate), `temporal` (resolver removed the current memory),
`entity` (wrong entity on top), `ranking` (retrieved but ranked too low),
`unknown`.

## Current top-line finding (bench 1.3 · dataset 0.3 · typedmem 0.8.0 @ 14f54b5)

82 tasks, k=5, seed=0. TypedMem current-state accuracy **0.79** vs. vector
**0.35**; stale-rate **0.00** vs. **0.37**. Of TypedMem's **17** failures,
**14 are `router`** (82%), 2 `ranking`, 1 `entity` — zero embedding/temporal.
The **v1.3 validation** shows **Rule + Global Fallback ≈ Oracle** (current-state
gap **+0.00** on the held-out eval set): routing is effectively solved by the
fallback, so an LLM router is **not** justified yet (decision **Case A** — freeze
routing, move to external baselines).
