# ReliAgent Bench — Memory Retrieval Benchmark Specification (v1.0)

**Status: frozen.** This document specifies ReliAgent Bench v1.0 — a reproducible
benchmark for evaluating whether an agent memory system retrieves the *currently
correct* memory as state evolves over time. It is implementation-agnostic:
TypedMem is the first reference system, but any system exposing
`retrieve(query, top_k) -> list[memory_id]` can be evaluated on the same tasks
with the same evaluator.

Companion docs: [`metrics.md`](metrics.md) (metric definitions), [`annotation.md`](annotation.md)
(labeling rules), [`roadmap.md`](roadmap.md).

---

## 1. Motivation

Existing memory benchmarks largely measure *semantic similarity* — can the system
find text related to the query? Long-running agents have a harder problem:
memory **changes over time**. A user who preferred startups in January prefers
mature companies in July; a dog that weighed 80 lb now weighs 75 lb; a project
that was *active* is now *archived*. A system that returns the *stale* memory is
wrong even though it is semantically similar. ReliAgent Bench measures **retrieval
correctness under change**, not similarity.

## 2. Benchmark philosophy

Retrieval correctness > semantic similarity. Concretely, the benchmark rewards:

- **Current-state retrieval** — returning the memory that is true *now*.
- **Stale avoidance** — never surfacing a superseded/out-of-date memory.
- **Evolving preferences / goals / decisions** — later statements supersede earlier ones.
- **Temporal reasoning** — supersession and recency, not just cosine similarity.
- **Entity precision** — distinguishing similar entities (Apple the company vs. the fruit).

A system can have perfect recall of "related" memories and still fail the
benchmark by ranking a stale memory first.

## 3. Dataset design

104 hand-authored tasks across **12 categories**. Each task is a small labeled
world: a set of memory records, one query, and ground-truth `relevant_ids`
(current/correct) and `stale_ids` (superseded). Categories and why they exist:

| Category | Retrieval challenge it introduces |
|---|---|
| `preference_evolution` | a preference changes; return the latest |
| `goal_evolution` | goals supersede one another over time |
| `decision_retrieval` | a decision is reconsidered; return the final one |
| `temporal_updates` | a fact is overwritten (weight, price, version) |
| `entity_disambiguation` | similar entities share a surface form |
| `status_tracking` | state transitions (active → paused → archived) |
| `long_history_retrieval` | one current answer among many distractors |
| `contradictions` | a later statement explicitly corrects an earlier one |
| `cross_session` | evidence spans sessions with long time gaps |
| `mixed_type` | the answer spans more than one memory type |
| `implicit_goal` | a goal question phrased without goal keywords (routing stress) |
| `implicit_decision` | a decision question phrased without decision keywords |

The last three deliberately stress *routing*: their queries are phrased so a
keyword router mis-classifies them (e.g. "What is the user focused on?" reads as
a `fact` question but the answer is a `goal`).

Data is **synthetic and hand-authored** — realistic but short and clean. This is
a demonstration-grade benchmark, not a corpus mined from real conversations.

## 4. Annotation guidelines

See [`annotation.md`](annotation.md). Summary:

- **Expected answer / current state** — the memory that is true as of "now"
  (the latest non-superseded memory for that subject) is `relevant`.
- **Superseded memories** — earlier versions are `stale` and carry
  `superseded_by` pointing at their replacement.
- **Multi-type queries** — a `mixed_type` task marks all types that a correct
  answer must cover; perfect routing must search all of them.
- **Acceptable retrieval** — top-1 should be a `relevant` memory; no `stale`
  memory should appear in the top-k.

## 5. Evaluation metrics

Full definitions and formulas in [`metrics.md`](metrics.md). Retrieval:
**Recall@K, Precision@K, MRR, NDCG@K**. Memory-specific: **Current-State
Accuracy** (top-1 is a current memory), **Wrong-Memory Rate**, **Stale-Memory
Rate**. Router study: **Oracle Gap** (Oracle metric − variant metric) plus
exact/acceptable type accuracy, exclusion/empty/fallback rates.

## 6. Failure attribution

Every failure of the target system is traced through the public retrieval stages
and assigned exactly one cause:

- **router** — the type filter removed the relevant memory (routing/filter).
- **embedding** — the relevant memory never entered the vector candidate set.
- **temporal** — the resolver removed the current memory.
- **entity** — the top result belongs to the wrong entity.
- **ranking** — the relevant memory was retrieved but ranked below the cutoff.
- **unknown** — none of the above.

Attribution replays the stages in order and blames the first stage at which the
relevant memory drops out. This doubles as a per-stage contribution estimate.

## 7. Versioning & reproducibility

Every run records: **benchmark version**, **dataset version**, **TypedMem
version + commit**, **ReliAgent Bench commit**, **configuration** (k, embedder,
dim), and **random seed**. Records are preserved per version under
`analysis/benchmark_history/` for regression analysis.

The dataset is **frozen** as v1.0: `datasets/FROZEN_MANIFEST.json` pins the task
count, per-category counts, task ids, and a content hash; a test fails if the
loaded dataset diverges. Future changes create a new dataset version rather than
editing v1.0.

**Reproduce the entire benchmark deterministically with one command:**

```bash
pip install -e . && python -m reliagent_bench.memory --validate --k 5 --seed 0
```

The embedder is a pure hash (no network, no randomness), so results are
bit-reproducible. Committed expected outputs live in
`src/reliagent_bench/memory/results/` and `analysis/`.

## 8. Scope & non-goals

This is a **v0 demonstration benchmark**: 104 synthetic tasks, a deliberately
weak deterministic embedder, internal baselines only. It does **not** claim any
system beats another in general, and it does not yet include external systems
(Mem0, LangMem, Zep) or real-conversation data — those are future milestones.
