# Memory Retrieval Benchmark (v0)

**Research question:** on memory that changes over time, does *typed* retrieval
return more correct memories than *vector-only* retrieval?

This is a **v0 benchmark and reproducible demonstration** — **not** a definitive
or general-purpose memory benchmark. The dataset is **42 hand-labeled synthetic
tasks across nine categories** (target: ~100), so every number here is
**preliminary**. We do **not** claim TypedMem outperforms vector-memory systems
in general. The narrow, supported finding is:

> On the included temporal and state-evolution tasks, TypedMem's temporal
> **resolver eliminates stale-memory retrieval and improves current-state
> accuracy** relative to the **included internal baselines**.

## The three arms

| Arm | Pipeline |
|---|---|
| `vector` | embed → top-k over all memories |
| `vector_filter` | typed routing → metadata filters → vector → top-k |
| `typedmem` | router → filters → vector → **temporal resolution** → rerank → top-k |

**Fairness:** all three arms run against the **same** per-task store, the same
query set, the same embedder instance, the same top-k, and the same evaluator.
The only thing that varies is the retrieval logic. TypedMem is called through its
**public API only** — no internals are copied, and TypedMem is not modified.

## Reproduce

```bash
pip install -e .                                   # pulls in typedmem>=0.8.0
python -m reliagent_bench.memory --k 5 --seed 0    # headline 3-arm comparison
python -m reliagent_bench.memory --k 5 --seed 0 --ablation   # stage ablation
python -m reliagent_bench.memory --k 5 --seed 0 --json       # per-query results
```

Runs are deterministic (pure-hash embedder). A committed copy of the output
lives in [`results/`](results/) so you can see the evidence without running.

**TypedMem used for the committed run:** version **0.8.0**, commit
[`14f54b5`](https://github.com/canis-minor/typedmem/commit/14f54b5) ·
embedder `hashing:dim=1024;ngram=2` · k=5 · seed=0.

## Results (seed dataset, 42 tasks, k=5, seed=0)

| System | Recall@5 | Prec@5 | MRR | NDCG | Wrong-rate ↓ | Stale-rate ↓ | Cur-state ↑ |
|---|---|---|---|---|---|---|---|
| vector | **0.98** | 0.45 | 0.64 | 0.72 | 0.55 | 0.37 | 0.31 |
| vector_filter | 0.90 | 0.43 | 0.58 | 0.67 | 0.48 | 0.34 | 0.29 |
| typedmem | 0.90 | **0.74** | **0.88** | **0.89** | **0.17** | **0.00** | **0.86** |

Note the **recall regression** (1.00 → 0.91): typed filtering is not free. The v0
router's broad `what is → fact` rule mis-routes some goal/status queries and the
type filter then drops the correct memories (see failure examples). This is a
real, benchmark-surfaced cost — reported, not hidden.

### Per category (Recall@5 / Stale-rate / Cur-state)

| Category | vector | vector_filter | typedmem |
|---|---|---|---|
| preference_evolution | 1.00 / 0.50 / 0.80 | 1.00 / 0.50 / 0.80 | 1.00 / **0.00** / **1.00** |
| goal_evolution | 1.00 / 0.53 / 0.40 | 0.80 / 0.43 / 0.20 | 0.80 / **0.00** / 0.80 |
| decision_retrieval | 1.00 / 0.30 / 0.00 | 1.00 / 0.30 / 0.00 | 1.00 / **0.00** / 0.60 |
| temporal_updates | 1.00 / 0.40 / 0.20 | 1.00 / 0.40 / 0.20 | 1.00 / **0.00** / **1.00** |
| entity_disambiguation | 1.00 / 0.07 / 1.00 | 1.00 / 0.07 / 1.00 | 1.00 / **0.00** / 1.00 |
| status_tracking | 1.00 / 0.50 / 0.00 | 0.40 / 0.20 / 0.00 | 0.40 / **0.00** / 0.40 |
| long_history_retrieval | 0.75 / 0.20 / 0.00 | 1.00 / 0.28 / 0.00 | 1.00 / **0.00** / **1.00** |
| contradictions | 1.00 / 0.50 / 0.00 | 1.00 / 0.50 / 0.00 | 1.00 / **0.00** / **1.00** |
| cross_session | 1.00 / 0.33 / 0.25 | 1.00 / 0.42 / 0.25 | 1.00 / **0.00** / **1.00** |

The **ablation** (`--ablation`) attributes the gains to the **resolver**: adding
it alone takes stale-rate to 0 and lifts current-state accuracy sharply. The new
categories are where typed retrieval helps most: on `long_history_retrieval`,
`contradictions`, and `cross_session`, TypedMem reaches 1.00 current-state while
vector-only sits at 0.00–0.33. Entity disambiguation shows no typed advantage —
v0 has no entity linking.

### Concrete examples

**Successes** (TypedMem returns the current memory; vector surfaces the stale one)
- `temp-01` — *"What is the dog's current weight?"* `80 lb` (Jan, superseded) → `75 lb` (Jul). vector's top-k includes the stale `80 lb`; typedmem returns only `75 lb`.
- `lhist-01` — *"What is the user's current job title?"* Among ~7 memories (hobbies, pets, events, an old title, the new title), typedmem filters to facts and resolves supersession → returns `Staff Engineer`; vector surfaces the stale `Junior Engineer` amid distractors.

**Failures** (surfaced by the benchmark)
- `goal-03` — *"What is the user currently saving money for?"* typedmem returns **`[]`**: the router maps `what is` → `fact`, and the type filter removes the goal-typed memories entirely. Router over-filtering — the same rule empties `stat-03` and `stat-04`.
- `dec-01` — *"Why did the user reject the Espresso Inc offer?"* typedmem returns both decision memories but ranks the neutral *"Considered the offer"* above *"Rejected … because the salary was below market"* — a ranking miss on the weak hashing embedder.

## Analysis (v1.1): metadata, difficulty & failure classification

Run with `--save-analysis` to write versioned artifacts under
[`../../../analysis/`](../../../analysis/) — history records (with benchmark /
dataset / TypedMem versions + commit hashes + config + seed + metrics),
per-category improvement tables, and a classified failure report — so results are
comparable across versions and engineering is driven by evidence.

- **Structured metadata.** Every task carries `difficulty` (easy / medium /
  hard), `required_capabilities`, `expected_memory_type`, and
  `requires_{temporal,entity,conflict}_resolution` — spelled out in the JSONL or
  derived from task shape.
- **Failure taxonomy.** Each TypedMem failure is traced through the public stages
  and labeled `router` / `embedding` / `temporal` / `entity` / `ranking` /
  `unknown`, with a root cause and a candidate fix; the runner summarizes counts
  by type and by stage.

**Current failure breakdown (42 tasks):** 6 TypedMem failures — **4 `router`**
(the `what is → fact` over-filtering) and **2 `ranking`**; zero embedding /
temporal / entity. That evidence — not intuition — points the next milestone at
the router.

## Router experiment (v1.2)

Because failure analysis flagged the router, we benchmark routing *strategies*
(the resolver and ranker stay fixed) on a deterministic, category-stratified
dev/eval split. TypedMem is **not** modified — routers are injected into the
pipeline via the public stage functions (`RouterPipelineRetriever`). Only after a
router wins consistently should it become a TypedMem default.

```bash
python -m reliagent_bench.memory --router-matrix --k 5 --seed 0 [--save-analysis]
```

Variants: **A** hard rule (baseline) · **B** no router (control) · **C** soft
top-N · **D** rule + global fallback · **Oracle** (labeled-type ceiling). **E**
(LLM: structured output, temp=0, versioned prompt, cached replay) and **F**
(hybrid: rule, LLM only when unconfident) are implemented but need an LLM
client/cache, so they are excluded from the offline run.

**Held-out eval finding (committed run in [`../../../analysis/router_reports/`](../../../analysis/router_reports/)):**

| Variant | Recall | Cur-state | Excl-rate | Empty-rate |
|---|---|---|---|---|
| A rule (hard) | 0.93 | 0.87 | 0.07 | 0.07 |
| **B none** | **1.00** | **0.93** | 0.00 | 0.00 |
| C soft top-2 | 0.93 | 0.87 | 0.07 | 0.07 |
| **D rule + fallback** | **1.00** | **0.93** | 0.07 | **0.00** |
| Oracle (ceiling) | 1.00 | 0.93 | 0.00 | 0.00 |

Reading (still preliminary, small eval set): **hard routing (A) costs recall**;
the **global fallback (D) recovers it to the no-router ceiling while keeping typed
precision and zero stale**; **soft top-N (C) does not help** — it cannot fix a
*confident* mis-route. Stale-rate is 0.00 everywhere (resolver unchanged). The
evidence favors **D (rule + fallback)** over the current hard router — but the
decision is deferred until the dataset nears 100 tasks and E/F are run, per the
milestone (no auto-selection of the top scorer).

## Limitations

- **Dataset size.** 42 tasks — a step toward the ~100-task target, still small.
  Enough to demonstrate the harness and produce directional signal; **not** enough
  for statistical claims. Treat all numbers as preliminary.
- **Synthetic data.** Every task is hand-authored, not drawn from real
  conversations. Content is short and clean, which flatters exact-token retrieval
  and does not exercise paraphrase, noise, or long context.
- **Weak embedder.** The default is a zero-dependency feature-hashing embedder,
  chosen for determinism, not quality. Absolute scores are illustrative; the
  **framework**, not any single number, is the deliverable.
- **Internal baselines only.** Comparisons are against in-repo vector baselines,
  **not** external systems (Mem0, LangMem, Zep, Letta) — intentionally out of
  scope until the harness stabilizes.

## Roadmap

1. **Dataset expansion** — grow toward 100 → 250 → 500 real retrieval problems
   (33 hand-labeled so far, nine categories). Real-embedder runs; held-out labels.
2. **Router improvement** — fix the over-eager `what is → fact` routing that
   causes the recall regression and empties some status/goal queries. Per the
   milestone, changes to TypedMem retrieval should be justified by measurable
   gains *on this benchmark*.
3. **External baselines** — add Mem0 / LangMem / Zep / Letta adapters behind the
   same `retrieve(query, top_k)` interface, once v0 is stable, on identical
   dataset / evaluator / metrics / top-k / embedding.
4. **Real-conversation evaluation** — replace synthetic tasks with labeled
   memories mined from real multi-session transcripts.

## License & contributing

Apache-2.0 (see [`../../../LICENSE`](../../../LICENSE)). Contributions welcome —
see [`../../../CONTRIBUTING.md`](../../../CONTRIBUTING.md). New retrieval systems
should implement `retrieve(query, top_k) -> list[str]` and plug in as a
`(name, factory)` system; new tasks are one JSONL line in `datasets/`.
