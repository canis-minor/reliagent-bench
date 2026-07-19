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
    p.add_argument("--router-matrix", action="store_true",
                   help="run the router experiment (variants A-D + Oracle) on a dev/eval split")
    p.add_argument("--validate", action="store_true",
                   help="run v1.3 validation: Oracle gap + failure distribution + stability + decision")
    p.add_argument("--json", action="store_true", help="emit full per-query results as JSON")
    p.add_argument("--save-analysis", action="store_true",
                   help="write versioned history + category/failure reports under analysis/")
    args = p.parse_args(argv)

    tasks = load_tasks(args.dataset)

    if args.router_matrix:
        _run_router_matrix(tasks, args)
        return

    if args.validate:
        _run_validation(tasks, args)
        return

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


def _run_router_matrix(tasks, args) -> None:
    from .history import ANALYSIS_DIR
    from .router_experiment import (
        default_variants,
        render_report,
        run_router_matrix,
        split_tasks,
    )

    dev, ev = split_tasks(tasks, eval_fraction=0.3, seed=args.seed)
    variants = default_variants(tasks)
    dev_results = run_router_matrix(dev, variants, k=args.k, seed=args.seed, embedder_dim=args.dim)
    eval_results = run_router_matrix(ev, variants, k=args.k, seed=args.seed, embedder_dim=args.dim)
    report = render_report(dev_results, eval_results, k=args.k, seed=args.seed,
                           num_dev=len(dev), num_eval=len(ev))
    print(report)
    if args.save_analysis:
        out_dir = ANALYSIS_DIR / "router_reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"router_matrix_k{args.k}_seed{args.seed}.md"
        path.write_text(report, encoding="utf-8")
        print(f"\n_router matrix written to {path}_")


def _run_validation(tasks, args) -> None:
    from .history import ANALYSIS_DIR, write_history_record
    from .validate import render_validation, run_validation

    v = run_validation(tasks, k=args.k, seed=args.seed, embedder_dim=args.dim)
    report = render_validation(v)
    print(report)
    if args.save_analysis:
        write_history_record(v.history_record)
        out_dir = ANALYSIS_DIR / "validation_reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"validation_ds{v.dataset_version}_k{args.k}_seed{args.seed}.md"
        path.write_text(report, encoding="utf-8")
        print(f"\n_validation written to {path}; history record updated_")


if __name__ == "__main__":
    main()
