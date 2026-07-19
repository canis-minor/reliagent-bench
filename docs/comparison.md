# Cross-System Comparison (ReliAgent Bench v1.0)

**Goal:** understand how different memory architectures behave on the *same*
frozen benchmark — comparative research, not a leaderboard race. Negative and
unexpected results are valuable; the benchmark stays architecture-neutral.

## Method

Every system implements one interface:

```python
def retrieve(query: str, top_k: int) -> list[str]:  # returns memory ids
    ...
```

For each task the system ingests that task's memories (each tagged with its
benchmark id), answers the query, and is scored by the **same** evaluator, on the
**same** dataset, with the **same** top-k. Built-in systems (`vector`,
`vector_filter`, `typedmem`) embed with the deterministic hashing embedder;
external systems embed internally with their own defaults (reasonable config, not
tuned for the benchmark).

Failures are classified **system-agnostically** from outputs alone, so the same
labels apply to a glass-box system (TypedMem) and a black-box one (Mem0):

- `stale` — surfaced an out-of-date (superseded) memory.
- `missed` — the relevant memory never appeared in the top-k.
- `entity` — top result belongs to the wrong entity.
- `mis_ranked` — relevant retrieved but not ranked first.

Run it:

```bash
python -m reliagent_bench.memory --audit                       # Stage 0 audit
python -m reliagent_bench.memory --compare --k 5 --seed 0 --save-analysis
```

Committed outputs: `analysis/comparison_reports/` (report + `environment.json`).

## Current results — built-in systems (104 tasks, k=5, seed=0)

Failure heatmap (counts, lower is better):

| System | stale | missed | entity | mis_ranked | total |
|---|---:|---:|---:|---:|---:|
| vector | 85 | 0 | 1 | 2 | 88 |
| vector_filter | 64 | 21 | 1 | 2 | 88 |
| typedmem | **0** | 21 | 1 | 2 | **24** |

The comparison already shows a clear **architectural tradeoff**, not just a score:

- **Vector-only** never *misses* (0) — it retrieves everything relevant — but
  surfaces the **stale** memory 85 times. It has no notion of "current".
- **TypedMem** eliminates stale retrieval (**0**) via temporal resolution, at the
  cost of 21 **missed** cases — all from the router over-filtering (the
  `what is → fact` mis-route), exactly as the router study found. Net failures
  drop from 88 → 24.
- **Typed filtering alone** (`vector_filter`) is strictly worse than either: it
  still surfaces stale memories (no resolver) *and* misses (the filter).

RQ4 preview: TypedMem's advantage on this benchmark comes from **temporal
resolution** (stale → 0), not from typed filtering (which, alone, hurts).

## External systems (Mem0 / LangMem / Zep) — pending

Adapters exist in [`../src/reliagent_bench/memory/external.py`](../src/reliagent_bench/memory/external.py)
behind the same interface, gated on package + credentials. They are **not run in
CI** — each needs its package plus a live service / API key (Mem0 → an LLM +
vector store; LangMem → an LLM; Zep → a Zep server). To evaluate one:

```bash
pip install mem0ai            # or: langmem / zep-cloud
export OPENAI_API_KEY=...     # Mem0/LangMem;  ZEP_API_KEY=... for Zep
python -m reliagent_bench.memory --compare --save-analysis
```

The registry auto-includes any system whose package + config is present; missing
systems are skipped (never faked). The adapters are **experimental/unverified** —
confirm the two or three marked API calls against your installed version, since
those APIs change between releases.

> The results above are the internal baselines only. Real Mem0/LangMem/Zep
> numbers, the full four-way category leaderboard, and the cross-architecture
> comparative analysis are the remaining work for this milestone and require an
> environment with those systems installed and credentialed.
