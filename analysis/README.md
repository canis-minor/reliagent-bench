# Analysis

Versioned benchmark history and failure analysis — the artifacts that make the
benchmark, not intuition, the source of engineering decisions.

```text
analysis/
    benchmark_history/   run records: benchmark/dataset/typedmem versions,
                         commit hashes, config, seed, overall metrics, failures
    category_reports/    per-category baseline→target improvement tables
    failure_reports/     every target-system failure, classified with a fix
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

## Current top-line finding (bench 1.1 · dataset 0.2 · typedmem 0.8.0 @ 14f54b5)

42 tasks, k=5, seed=0. TypedMem current-state accuracy **0.86** vs. vector
**0.31**; stale-rate **0.00** vs. **0.37**. Of TypedMem's **6** failures,
**4 are `router`** (the `what is → fact` over-filtering) and **2 are `ranking`**
— zero embedding/temporal/entity. This concentrates the next milestone squarely
on the **router**, with evidence rather than intuition.
