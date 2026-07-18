from agent_benchmark import BenchmarkScore, aggregate_scores


def test_aggregate_scores() -> None:
    result = aggregate_scores([
        BenchmarkScore(1, 1, 0.8, 1, 0.1, 1000),
        BenchmarkScore(0, 0.5, 0.6, 1, 0.2, 2000),
    ])
    assert result["task_success"] == 0.5
    assert result["latency_ms"] == 1500
