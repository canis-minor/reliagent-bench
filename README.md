> This repository is part of the **[Reliable Long-Running Agents (RLRA)](https://github.com/canis-minor)** research initiative.

# ReliAgent Bench

**A reproducible reliability benchmark for long-running, tool-using, memory-enabled agents.**

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

A **v0 benchmark and reproducible demonstration** — not yet a definitive or
general-purpose memory benchmark. It runs three arms — vector-only, vector +
typed filters, and the full TypedMem pipeline — over **33 hand-labeled synthetic
tasks across nine categories**, so results are **preliminary**. Full details,
results, examples, and limitations:
[`src/reliagent_bench/memory/README.md`](src/reliagent_bench/memory/README.md);
a committed run is in [`src/reliagent_bench/memory/results/`](src/reliagent_bench/memory/results/).

```bash
pip install -e .                                 # pulls in typedmem>=0.8.0
python -m reliagent_bench.memory --k 5 --seed 0  # 3-arm comparison
python -m reliagent_bench.memory --k 5 --seed 0 --ablation
```

**Narrow finding (not a general claim):** on the included temporal and
state-evolution tasks, TypedMem's resolver takes stale-memory retrieval from 37%
(vector) to **0%** and current-state accuracy from 30% to **85%** vs. the
included internal baselines. Typed filtering also causes a **recall regression**
(1.00 → 0.91) from v0 router over-filtering. Run against `typedmem` 0.8.0
(commit `14f54b5`), hashing embedder, k=5, seed=0.

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
