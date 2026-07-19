# Memory Retrieval Track

The first ReliAgent Bench track: **does typed retrieval beat vector-only retrieval?**

It compares three retrieval arms on the same hand-labeled tasks, using
[TypedMem](https://github.com/canis-minor/typedmem)'s **public API only**
(TypedMem does not depend on this package):

| Arm | Pipeline |
|---|---|
| `vector` | embed → top-k over all memories |
| `vector_filter` | typed routing → metadata filters → vector → top-k |
| `typedmem` | router → filters → vector → **temporal resolution** → rerank → top-k |

## Run it

```bash
pip install -e .                       # pulls in typedmem>=0.8.0
python -m reliagent_bench.memory        # headline 3-arm comparison
python -m reliagent_bench.memory --ablation   # stage ablation
python -m reliagent_bench.memory --json > run.json   # full per-query results
```

Flags: `--k`, `--seed`, `--dim` (embedding size), `--dataset PATH`.

## Design

Concerns are separated so future memory systems can plug in without touching the
evaluator:

- `dataset.py` — declarative JSONL tasks → a fresh TypedMem store (inserted
  verbatim via `create` transitions, so the labeled timeline is preserved).
- `baselines.py` — the three arms + a configurable `AblationRetriever`; common
  interface `retrieve(query, top_k) -> list[str]`.
- `metrics.py` — Recall@K, Precision@K, MRR, NDCG, plus memory-specific
  **wrong-memory rate**, **stale-memory rate**, **current-state accuracy**, and
  **entity-resolution accuracy**.
- `evaluator.py` / `runner.py` — per-query scoring and aggregation. Runs are
  deterministic (pure-hash embedder) and record their full config + seed.
- `report.py` — comparison table, per-category breakdown, and failure examples.

All arms share the same store, query, embedder instance, top-k, and evaluator, so
differences come only from the retrieval logic.

## Dataset

`datasets/seed.jsonl` — 18 hand-labeled tasks across six categories: preference
evolution, goal evolution, decision retrieval, temporal updates, entity
disambiguation, status tracking. Each task labels `relevant_ids` (current) and
`stale_ids` (superseded/out-of-date). Quality over size by design — extend it
before scaling it.

Mapping to the TypedMem model: an "entity" is `Memory.subject`; temporal validity
is `timestamp` + `superseded_by` (there are no separate `valid_from/valid_to`
fields).

## Initial findings (illustrative)

With the zero-dependency hashing embedder and the seed set (k=5, seed=0):

| System | Recall@5 | Prec@5 | Stale-rate | Cur-state |
|---|---|---|---|---|
| vector | 1.00 | 0.49 | **0.37** | 0.33 |
| vector_filter | 0.89 | 0.44 | 0.31 | 0.28 |
| typedmem | 0.89 | **0.75** | **0.00** | **0.78** |

- **Temporal resolution is the dominant win** — the ablation shows `+resolver`
  alone drives stale-rate to 0 and current-state accuracy to 0.78. TypedMem never
  surfaces a superseded memory; vector-only does 37% of the time.
- **Typed filtering via the v0 router is a mixed bag** — the router's broad
  `what is → fact` rule over-filters some goal/status queries (recall 1.00 →
  0.89). This is the first *benchmark-driven* candidate for improving TypedMem's
  router, and per the milestone it should only change if it shows measurable
  gains here.

> Numbers are illustrative: the hashing embedder is deliberately weak. The
> framework — not any single score — is the deliverable. External libraries
> (Mem0, LangMem, Zep, Letta) are intentionally out of scope until the harness
> is stable.
