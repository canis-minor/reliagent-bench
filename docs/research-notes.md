# Research Notes — TypedMem × ReliAgent Bench (First Cycle)

*Status: living document. Foundation for future technical articles, papers, and
external-system comparisons. All quantitative claims are **preliminary**: they
come from a 104-task synthetic benchmark scored with a deterministic
feature-hashing embedder (k=5, seed=0, `typedmem` 0.8.0 @ `14f54b5`). The
framework — not any single score — is the contribution.*

---

## 1. Framing

Most agent-memory demos work once. The open problem is **reliability over time**:
as an agent accumulates memories, does it retrieve the one that is *currently
correct* when the world has changed? A user who preferred startups in January
prefers mature companies in July; a dog that weighed 80 lb now weighs 75 lb; a
project that was *active* is now *archived*. A system that returns the *stale*
memory is wrong even though it is semantically similar.

This cycle pursued a single method: **benchmark-driven development**. Build a
memory architecture (TypedMem), build an architecture-neutral benchmark
(ReliAgent Bench), and let the benchmark — not intuition — decide what to build
next. Every architectural claim below is tied to a reproducible experiment.

## 2. Hypotheses

- **H1 (typed retrieval).** Retrieving over *typed, temporal, provenance-aware*
  memory beats vector-only retrieval on correctness-under-change.
- **H2 (temporal resolution).** The specific mechanism that matters is temporal
  resolution (dropping superseded memories), not merely typing.
- **H3 (typed filtering).** Restricting search to a predicted memory type
  improves precision without hurting recall.
- **H4 (routing).** A smarter router (soft top-N, or an LLM) is needed to fix
  routing errors.

H1 and H2 were supported; **H3 and H4 were falsified** by the benchmark — the
valuable surprises of this cycle.

## 3. Experiments (the milestone arc)

| Milestone | Question | Method |
|---|---|---|
| v0.8 kernel | can mutation be made auditable + concurrent? | TransitionEngine, versions, injectable strategies |
| v0.9 retrieval | does typed retrieval beat vector-only? | 3-arm pipeline (vector / +filter / typed) |
| v1.0 benchmark | how to measure correctness-under-change? | metrics + seed dataset + ablation |
| v1.1 failure attribution | *why* does it fail? | stage-traced failure classifier |
| v1.2 router study | which routing strategy is best? | matrix A–F + Oracle, dev/eval split |
| v1.3 validation | does the conclusion hold at scale? | Oracle Gap + stability, 42→82 tasks |
| v1.4 freeze | is the benchmark trustworthy? | 104 tasks, manifest, spec, freeze |
| v1.5 cross-system | how do architectures differ? | agnostic failure heatmap + adapters |

## 4. Headline results (ReliAgent Bench v1.0, 104 tasks)

| System | Recall@5 | Prec@5 | Stale-rate ↓ | Current-state ↑ |
|---|---:|---:|---:|---:|
| vector | **0.99** | 0.48 | 0.36 | 0.38 |
| vector + typed filter | 0.79 | 0.40 | 0.28 | 0.32 |
| TypedMem (full) | 0.79 | **0.66** | **0.00** | **0.77** |

System-agnostic failure heatmap (counts; computed from outputs, so it applies to
any system):

| System | stale | missed | entity | mis-ranked | total |
|---|---:|---:|---:|---:|---:|
| vector | 85 | 0 | 1 | 2 | 88 |
| vector + filter | 64 | 21 | 1 | 2 | 88 |
| TypedMem | **0** | 21 | 1 | 2 | **24** |

## 5. Surprising findings

1. **The win is temporal resolution, not typing (H2 ✓, H3 ✗).** Vector-only
   *never misses* (recall 0.99) but surfaces a stale memory 85×. TypedMem drives
   stale retrieval to **0** and roughly doubles current-state accuracy — but
   **typed filtering *alone* is strictly worse** than either extreme: it still
   surfaces stale memories (no resolver) *and* newly misses (the filter). The
   resolver, not the filter, is the value.

2. **Hard routing is the dominant failure, and it is self-inflicted.** Of
   TypedMem's 24 failures, **21 (88%) are routing** — almost entirely one rule:
   a query like "What is the user focused on?" reads as a `fact` question, so the
   type filter deletes the goal memories and the pipeline returns nothing. The
   architecture's own filter is its top failure mode.

3. **Soft top-N routing does not help (H4 ✗, part 1).** It cannot fix a
   *confident* mis-route — the router is sure the query is a `fact`, and taking
   the top-2 predicted types still doesn't include `goal`.

4. **A global fallback matches the Oracle (H4 ✗, part 2).** Adding a small
   unrestricted semantic search alongside the typed search (variant D) closes the
   current-state gap to the Oracle router to **+0.00** on the held-out eval set —
   the same as removing the router entirely. An **LLM router is not justified** by
   the benchmark. A trivial mechanism beats a sophisticated one.

5. **Category structure reveals where architecture matters (RQ2/RQ3).**
   - Temporal resolution dominates: `contradictions`, `long_history`,
     `temporal_updates`, `cross_session` → TypedMem **1.00** vs vector 0.00–0.40.
   - No typed advantage: `entity_disambiguation` (0.92 for all) — v0 has no
     entity linking.
   - Hard for everyone: `status_tracking` (≤0.18), `implicit_goal` (0.25) — the
     stale memory is too similar to the query for either approach.
   - **A striking negative result:** `implicit_decision` — vector **1.00**,
     TypedMem **0.00**. The router over-filters these queries to oblivion; the
     "dumber" system wins outright.

6. **The conclusions were stable as the benchmark grew** (42 → 82 → 104 tasks):
   stale-rate 0.00 throughout, router the dominant failure (67% → 82% → 88%), and
   Rule+Fallback ≈ Oracle at every size. Growth *sharpened* the router finding
   rather than overturning it.

## 6. Architectural decisions (each backed by evidence)

- **A kernel that separates mechanism from policy** (v0.8): a single
  `TransitionEngine` is the only mutator; identity/confidence/lifecycle are
  injectable strategies; every memory carries a version for optimistic
  concurrency. Rationale: make evolution auditable and testable before optimizing
  numbers.
- **Temporal resolution is core; typed filtering is provisional.** The benchmark
  says the resolver earns its place and the hard filter does not (net-negative
  in isolation). So the filter should be *softened by a global fallback*, not
  made smarter.
- **Do not add an LLM router.** Decision **Case A**: freeze routing research; the
  fallback already reaches the Oracle ceiling. This is the clearest example of the
  benchmark *preventing* a feature.
- **Freeze the benchmark before external comparison** (v1.0): a moving benchmark
  cannot fairly compare systems. Dataset, metrics, evaluation, and categories are
  pinned by a manifest + freeze test.

## 7. Remaining limitations / threats to validity

- **Synthetic, hand-authored data.** 104 short, clean tasks — not mined from real
  conversations. Content is exact-token-friendly, flattering both retrieval
  styles and under-testing paraphrase, noise, and long context.
- **Deliberately weak embedder.** A zero-dependency feature-hashing embedder was
  chosen for determinism, not quality; absolute scores are illustrative. A real
  embedder could move recall/ranking numbers materially.
- **Small, single-seed, single-k.** 104 tasks, seed=0, k=5. No confidence
  intervals; conclusions are directional.
- **Metric edge case.** `current_state_accuracy` = "top-1 is *a* relevant
  memory," which makes multi-answer `mixed_type` tasks trivially 1.00 — it does
  not check that *all* required types were returned. A stricter multi-answer
  metric is future work.
- **Internal baselines only.** No external systems have actually been run;
  Mem0/LangMem/Zep adapters exist but are unverified and need live services/keys.
- **Category imbalance.** Counts range 3–12 per category; per-category numbers on
  the smallest categories are noisy.

## 8. Open research questions

- **RQ-A.** Under a *real* embedder, does the resolver's advantage persist, and
  does the recall cost of typed filtering shrink (making the fallback less
  necessary)?
- **RQ-B.** Is there any query distribution where an LLM router beats
  Rule+Fallback enough to justify its latency/cost? (Current evidence: no.)
- **RQ-C.** What actually helps `status_tracking` and `implicit_goal`, the
  categories hard for every system? Ranking? Entity/state modeling?
- **RQ-D (external, pending).** Where do Mem0 / LangMem / Zep land on the failure
  heatmap — do LLM-summarizing memory systems avoid stale retrieval, or do they
  hallucinate a merged answer? Which categories separate architectural families?
- **RQ-E.** Does the "temporal resolution > typing" result generalize to
  real multi-session transcripts, or is it an artifact of clean supersession
  labels?

## 9. What this cycle contributes

Not "TypedMem beats everything." Rather: **a reproducible method for deciding
memory-architecture questions with evidence** — including three cases where the
benchmark *stopped* a plausible-sounding feature (smarter router, soft routing,
typed filtering as a net good). The durable artifacts are the frozen benchmark,
the failure taxonomy, and the decision record — reusable by any future memory
system, TypedMem included.

## 10. Next steps

1. **Validate the Mem0 adapter** against a specific supported version in an
   executable environment (package + LLM key), then run Stages 2–4 (Mem0 →
   LangMem → Zep) and produce the four-way leaderboard + heatmap.
2. **Real-embedder pass** to test RQ-A / RQ-E.
3. ~~Draft the first technical article~~ → **done:**
   [_How much does temporal reasoning actually help — and why didn't a smarter
   router?_](articles/01-does-temporal-reasoning-help.md).
4. Only then consider TypedMem changes — driven by gaps this analysis exposes
   (ranking for the hard categories; adopting the global fallback), not by
   proactive feature-building.
