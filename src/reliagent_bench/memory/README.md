# Memory Retrieval Benchmark (v0)

**Research question:** on memory that changes over time, does *typed* retrieval
return more correct memories than *vector-only* retrieval?

This is a **v0 benchmark and reproducible demonstration** — **not** a definitive
or general-purpose memory benchmark. The dataset is **18 hand-labeled synthetic
tasks**, so every number here is **preliminary**. We do **not** claim TypedMem
outperforms vector-memory systems in general. The narrow, supported finding is:

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

## Results (seed dataset, 18 tasks, k=5, seed=0)

| System | Recall@5 | Prec@5 | MRR | NDCG | Wrong-rate ↓ | Stale-rate ↓ | Cur-state ↑ |
|---|---|---|---|---|---|---|---|
| vector | **1.00** | 0.49 | 0.67 | 0.75 | 0.51 | 0.37 | 0.33 |
| vector_filter | 0.89 | 0.44 | 0.58 | 0.66 | 0.45 | 0.31 | 0.28 |
| typedmem | 0.89 | **0.75** | **0.83** | **0.85** | **0.14** | **0.00** | **0.78** |

Note the **recall regression** (1.00 → 0.89): typed filtering is not free. The v0
router's broad `what is → fact` rule mis-routes some goal/status queries and the
type filter then drops the correct memories (see failure examples). This is a
real, benchmark-surfaced cost — reported, not hidden.

### Per category (Recall@5 / Stale-rate / Cur-state)

| Category | vector | vector_filter | typedmem |
|---|---|---|---|
| preference_evolution | 1.00 / 0.50 / 0.67 | 1.00 / 0.50 / 0.67 | 1.00 / **0.00** / **1.00** |
| goal_evolution | 1.00 / 0.56 / 0.33 | 0.67 / 0.39 / 0.00 | 0.67 / **0.00** / 0.67 |
| decision_retrieval | 1.00 / 0.17 / 0.00 | 1.00 / 0.17 / 0.00 | 1.00 / **0.00** / 0.33 |
| temporal_updates | 1.00 / 0.50 / 0.00 | 1.00 / 0.50 / 0.00 | 1.00 / **0.00** / **1.00** |
| entity_disambiguation | 1.00 / 0.00 / 1.00 | 1.00 / 0.00 / 1.00 | 1.00 / 0.00 / 1.00 |
| status_tracking | 1.00 / 0.50 / 0.00 | 0.67 / 0.33 / 0.00 | 0.67 / **0.00** / 0.67 |

The **ablation** (`--ablation`) attributes the gains to the **resolver**: adding
it alone takes stale-rate to 0 and current-state accuracy to 0.78. Entity
disambiguation shows no typed advantage — v0 has no entity linking.

### Concrete examples

**Successes** (TypedMem returns the current memory; vector surfaces the stale one)
- `temp-01` — *"What is the dog's current weight?"* Memories: `80 lb` (Jan, superseded) → `75 lb` (Jul). vector's top-k includes the stale `80 lb`; typedmem returns only `75 lb`.
- `pref-01` — *"What kind of company does the user prefer to work at now?"* `startups` (Jan, superseded) → `mature companies` (Jul). typedmem drops the January preference; vector does not.

**Failures** (surfaced by the benchmark)
- `goal-03` — *"What is the user currently saving money for?"* typedmem returns **`[]`**: the router maps `what is` → `fact`, and the type filter removes the goal-typed memories entirely. Router over-filtering.
- `dec-01` — *"Why did the user reject the Espresso Inc offer?"* typedmem returns both decision memories but ranks the neutral *"Considered the offer"* above *"Rejected … because the salary was below market"* — a ranking miss on the weak hashing embedder.

## Limitations

- **Dataset size.** 18 tasks. Enough to demonstrate the harness and produce
  directional signal; **not** enough for statistical claims. Treat all numbers as
  preliminary.
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

1. **Dataset expansion** — more tasks per category, real-embedder runs, and
   held-out labeling; move from "demonstration" toward a benchmark.
2. **Router improvement** — fix the over-eager `what is → fact` routing that
   causes the recall regression. Per the milestone, changes to TypedMem
   retrieval should be justified by measurable gains *on this benchmark*.
3. **External baselines** — add Mem0 / LangMem / Zep / Letta adapters behind the
   same `retrieve(query, top_k)` interface, once v0 is stable.
4. **Real-conversation evaluation** — replace synthetic tasks with labeled
   memories mined from real multi-session transcripts.

## License & contributing

Apache-2.0 (see [`../../../LICENSE`](../../../LICENSE)). Contributions welcome —
see [`../../../CONTRIBUTING.md`](../../../CONTRIBUTING.md). New retrieval systems
should implement `retrieve(query, top_k) -> list[str]` and plug in as a
`(name, factory)` system; new tasks are one JSONL line in `datasets/`.
