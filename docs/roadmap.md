# Benchmark Roadmap

The living roadmap lives in [`../ROADMAP.md`](../ROADMAP.md). This note records
the frozen-benchmark milestone and what comes next.

## ReliAgent Bench v1.0 (frozen)

- 104 hand-authored tasks across 12 categories, `DATASET_VERSION = 1.0`.
- Metrics, evaluation logic, category definitions, and failure attribution are
  frozen; `datasets/FROZEN_MANIFEST.json` + the freeze test guard against drift.
- Validation confirms the v1.2/v1.3 routing conclusions hold at scale (see the
  committed validation report under `analysis/validation_reports/`).

Future changes create v1.1, v1.2, … rather than modifying v1.0.

## Next: external baselines (TypedMem v1.5)

With the benchmark frozen, the next milestone adds adapters for **Mem0**,
**LangMem**, and **Zep** behind the same `retrieve(query, top_k)` interface, run
on the **identical** dataset / evaluator / metrics / top-k / embedding model.
Only the memory system varies.

## Longer term

- Real-conversation evaluation (labeled memories mined from multi-session transcripts).
- Real-embedder runs alongside the deterministic hashing embedder.
- Public leaderboard protocol.

## Evolving mission: benchmark *persistent agent representations*, not only memory

ReliAgent Bench is broadening from "benchmark memory systems" to "evaluate persistent
agent representations." These are not one leaderboard — they answer different questions
and carry different metrics — so the benchmark holds multiple **tracks by
representation**, each independent:

| Track | Representation | Question | Metrics | Maturity |
|---|---|---|---|---|
| **A — Memory** | vector · Mem0 · LangMem · TypedMem | retrieves the right state? | recall / stale-rate / current-state acc. | **frozen v1.0** |
| **B — Operational provenance** | AgentTrace · LangSmith · OTel | reconstructs *what happened*? | localization of operational faults | design-stage |
| **C — Semantic provenance** | StateGraph · future systems | reconstructs *what was believed*? | localization / reproducibility / utility | design-stage → [`semantic-provenance-plan.md`](semantic-provenance-plan.md) |

Principle: the benchmark evaluates representations; it is not owned by any system it
evaluates (GLUE is not part of BERT). Track A stays frozen and backward-compatible;
new tracks are added alongside as separate suites, never by unfreezing v1.0.

Phasing: **1** Memory retrieval (done, frozen) → **2** Persistent state → **3**
Operational provenance → **4** Semantic provenance. A long-lived benchmark, not a v2.
