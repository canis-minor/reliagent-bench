> This repository is part of the **[Reliable Long-Running Agents (RLRA)](https://github.com/canis-minor)** research initiative.

# ReliAgent Bench

**A reproducible reliability benchmark for long-running, tool-using, memory-enabled agents.**

> **Boundary.** ReliAgent Bench evaluates persistent agent representations. It does not
> prescribe any particular representation.

![status: experimental](https://img.shields.io/badge/status-experimental-orange)

> Siblings in the RLRA stack —
> [TypedMem](https://github.com/canis-minor/typedmem) ·
> [AgentCheck](https://github.com/canis-minor/agentcheck) ·
> [AgentTrace](https://github.com/canis-minor/agenttrace) ·
> **ReliAgent Bench** ·
> [AgentLab](https://github.com/canis-minor/agentlab)

ReliAgent Bench compares complete agent *systems* rather than only base models.
It measures task completion, reliability, recovery, cost, latency, and memory
quality across multi-step scenarios.

> **Naming note.** Deliberately *not* named "AgentBench" — that name is already
> used by prior agent-benchmark research. ReliAgent Bench focuses specifically
> on the *reliability* of long-running agents.

## Benchmark dimensions

- Single-task correctness
- Long-horizon consistency
- Tool-selection accuracy
- Recovery from tool failure
- Memory retention and stale-memory handling
- Cost and latency
- Run-to-run variance

## Dataset format

```json
{
  "id": "calendar-conflict-001",
  "category": "tool_use",
  "turns": [],
  "checks": [],
  "fault_injection": {}
}
```

See `datasets/sample/` for a worked example.

## Initial benchmark tracks

1. Tool use
2. Long-horizon memory
3. Failure recovery
4. Policy adherence
5. Multi-step planning

## Reproducibility policy

Every published result should include:

- model and provider version;
- agent framework version;
- prompt and tool schema;
- run count;
- temperature and sampling settings;
- evaluator definition;
- raw trace location.

## Memory retrieval track (v0)

A **v0 benchmark and reproducible demonstration**, **frozen as ReliAgent Bench
v1.0** — not a definitive or general-purpose memory benchmark. It runs three arms
— vector-only, vector + typed filters, and the full TypedMem pipeline — over
**104 hand-labeled synthetic tasks across twelve categories**, with structured
metadata, difficulty levels, classified failure analysis, a router experiment,
Oracle-gap validation, and versioned run history under [`analysis/`](analysis/).
Results are **preliminary**. **Specification:** [`docs/benchmark.md`](docs/benchmark.md)
(+ [`metrics.md`](docs/metrics.md), [`annotation.md`](docs/annotation.md)).
**Research notes / first-cycle analysis:** [`docs/research-notes.md`](docs/research-notes.md).
**Article:** [_How much does temporal reasoning actually help — and why didn't a smarter router?_](docs/articles/01-does-temporal-reasoning-help.md).
Track details: [`src/reliagent_bench/memory/README.md`](src/reliagent_bench/memory/README.md).

```bash
pip install -e .                                 # pulls in typedmem>=0.8.0
python -m reliagent_bench.memory --k 5 --seed 0  # 3-arm comparison
python -m reliagent_bench.memory --k 5 --seed 0 --ablation
```

**Narrow finding (not a general claim):** on the included temporal and
state-evolution tasks, TypedMem's resolver takes stale-memory retrieval from 36%
(vector) to **0%** and current-state accuracy from 38% to **77%** vs. the
included internal baselines. Typed filtering causes a **recall regression**
(0.99 → 0.79) from router over-filtering. Validation across three versions
(42 → 82 → 104 tasks) shows **Rule + Global Fallback matches the Oracle ceiling
(current-state gap +0.00)** throughout — so routing is effectively solved by the
fallback and an **LLM router is not justified** (decision: freeze routing, move to
external baselines). Run against `typedmem` 0.8.0 (commit `14f54b5`), hashing
embedder, k=5, seed=0.

## Evaluation tracks (by representation)

ReliAgent Bench is broadening from "benchmark memory systems" to **evaluate persistent
agent representations** — held as independent tracks, since they answer different
questions and carry different metrics (they are *not* one leaderboard):

| Track | Representation | Question | Maturity |
|---|---|---|---|
| **A — Memory** | vector · Mem0 · LangMem · TypedMem | retrieves the right state? | **frozen v1.0** (above) |
| **B — Operational provenance** | [AgentTrace](https://github.com/canis-minor/agenttrace) · LangSmith · OTel | reconstructs *what happened*? | design-stage |
| **C — Semantic provenance** | [StateGraph](https://github.com/canis-minor/stategraph) · future systems | reconstructs *what was believed*? | design → [`docs/semantic-provenance-plan.md`](docs/semantic-provenance-plan.md) |

The benchmark evaluates representations; it is not owned by any system it evaluates
(GLUE is not part of BERT). Track A stays frozen; new tracks are added as separate
suites. See [`docs/roadmap.md`](docs/roadmap.md).

## Quick start

```bash
pip install -e .
python -c "from reliagent_bench import aggregate_scores"
```

## Status

**Experimental.** The **memory retrieval track** is implemented (three arms,
metrics, ablation, deterministic runner, per-query results, seed dataset). The
agent-track dataset schema and scoring scaffold (`aggregate_scores`) exist;
fault injection and the leaderboard protocol are not yet implemented. Task sets
are meant to be executed via [AgentCheck](https://github.com/canis-minor/agentcheck)
and traced with [AgentTrace](https://github.com/canis-minor/agenttrace).
