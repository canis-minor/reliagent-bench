"""CLI: run the memory-retrieval benchmark and print a report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .baselines import ABLATION_SYSTEMS, DEFAULT_SYSTEMS
from .dataset import DEFAULT_DATASET, load_tasks
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
    args = p.parse_args(argv)

    tasks = load_tasks(args.dataset)
    systems = ABLATION_SYSTEMS if args.ablation else DEFAULT_SYSTEMS
    result = run_benchmark(
        tasks, systems, k=args.k, seed=args.seed, embedder_dim=args.dim,
        dataset_name=Path(args.dataset).stem,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(render_report(result))


if __name__ == "__main__":
    main()
