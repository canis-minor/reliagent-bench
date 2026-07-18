from dataclasses import dataclass


@dataclass(slots=True)
class BenchmarkScore:
    task_success: float
    recovery: float
    memory_quality: float
    policy_adherence: float
    cost_usd: float
    latency_ms: float


def aggregate_scores(scores: list[BenchmarkScore]) -> dict[str, float]:
    if not scores:
        raise ValueError("scores must not be empty")
    count = len(scores)
    return {
        "task_success": sum(s.task_success for s in scores) / count,
        "recovery": sum(s.recovery for s in scores) / count,
        "memory_quality": sum(s.memory_quality for s in scores) / count,
        "policy_adherence": sum(s.policy_adherence for s in scores) / count,
        "cost_usd": sum(s.cost_usd for s in scores) / count,
        "latency_ms": sum(s.latency_ms for s in scores) / count,
    }
