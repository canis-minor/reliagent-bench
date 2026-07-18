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

## Quick start

```bash
pip install -e .
python -c "from reliagent_bench import aggregate_scores"
```

## Status

**Experimental.** Dataset schema, one sample task, and a scoring scaffold
(`aggregate_scores`) exist. The reproducible runner, fault injection, the memory
track, and the leaderboard protocol are not yet implemented. Task sets are meant
to be executed via [AgentCheck](https://github.com/canis-minor/agentcheck) and
traced with [AgentTrace](https://github.com/canis-minor/agenttrace).
