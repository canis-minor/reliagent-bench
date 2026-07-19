"""CLI: run the memory-retrieval benchmark, print a report, and analyze failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from typedmem import HashingEmbeddingProvider

from .analysis import (
    diagnose_all,
    render_category_improvement,
    render_failure_report,
)
from .baselines import ABLATION_SYSTEMS, DEFAULT_SYSTEMS
from .dataset import DEFAULT_DATASET, load_tasks
from .history import write_run_artifacts
from .report import render_report
from .runner import run_benchmark


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(
        prog="reliagent-bench-memory",
        description="Typed vs. vector memory-retrieval benchmark (TypedMem).",
    )
    p.add_argument("--dataset", default=str(DEFAULT_DATASET), help="path to a JSONL task file")
    p.add_argument("--k", type=int, default=5, help="top-k")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--dim", type=int, default=1024, help="embedding dimension")
    p.add_argument("--ablation", action="store_true", help="run the stage ablation, not the 3 arms")
    p.add_argument("--json", action="store_true", help="emit full per-query results as JSON")
    p.add_argument("--save-analysis", action="store_true",
                   help="write versioned history + category/failure reports under analysis/")
    args = p.parse_args(argv)

    tasks = load_tasks(args.dataset)
    systems = ABLATION_SYSTEMS if args.ablation else DEFAULT_SYSTEMS
    result = run_benchmark(
        tasks, systems, k=args.k, seed=args.seed, embedder_dim=args.dim,
        dataset_name=Path(args.dataset).stem,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    # Failure analysis for the target (last) system.
    target = result.config.systems[-1]
    embedder = HashingEmbeddingProvider(dim=args.dim)
    records = diagnose_all(tasks, embedder, result.per_query, target, args.k)
    category_md = render_category_improvement(result)
    failure_md = render_failure_report(records, target=target)

    print(render_report(result))
    print("\n## Analysis\n")
    print(category_md)
    print()
    print(failure_md)

    if args.save_analysis:
        path = write_run_artifacts(result, records, category_md=category_md, failure_md=failure_md)
        print(f"\n_analysis written under {path.parent.parent}/ (record: {path.name})_")


if __name__ == "__main__":
    main()
