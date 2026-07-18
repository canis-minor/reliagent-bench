# Agent Benchmark

A reproducible benchmark for long-running, tool-using, memory-enabled agents.

The benchmark is designed to compare complete agent systems rather than only
base models. It measures task completion, reliability, recovery, cost,
latency, and memory quality across multi-step scenarios.

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

## Status

Dataset schema, sample tasks, and scoring scaffold.
