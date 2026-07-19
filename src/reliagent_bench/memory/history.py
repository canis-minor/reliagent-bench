"""Versioned benchmark history + analysis artifacts.

Each run is preserved (not overwritten) keyed by benchmark/dataset/typedmem
version + config, so results are comparable across versions for regression
analysis. Artifacts land under ``<repo>/analysis/``:

    analysis/
        benchmark_history/   run records (version, commits, config, metrics)
        category_reports/    per-category improvement tables
        failure_reports/     failure analysis
        plots/               (reserved)
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import typedmem

from .analysis import failure_summary
from .dataset import DATASET_VERSION

BENCHMARK_VERSION = "1.1"

# repo root = .../reliagent-bench (dataset.py lives at src/reliagent_bench/memory/)
REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_DIR = REPO_ROOT / "analysis"


def _git_commit(path: Path | str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def _typedmem_commit() -> str | None:
    try:
        return _git_commit(Path(typedmem.__file__).resolve().parent)
    except Exception:
        return None


def build_history_record(result, records) -> dict:
    c = result.config
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "dataset_version": DATASET_VERSION,
        "dataset": c.dataset,
        "num_tasks": c.num_tasks,
        "typedmem_version": c.typedmem_version,
        "typedmem_commit": _typedmem_commit(),
        "reliagent_commit": _git_commit(REPO_ROOT),
        "config": {
            "k": c.k, "seed": c.seed,
            "embedder_id": c.embedder_id, "embedder_dim": c.embedder_dim,
            "systems": c.systems,
        },
        "overall": result.overall,
        "failures": {"total": len(records), "by_type": failure_summary(records)},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def run_slug(result) -> str:
    c = result.config
    return f"bench{BENCHMARK_VERSION}_ds{DATASET_VERSION}_tm{c.typedmem_version}_{c.dataset}_k{c.k}_seed{c.seed}"


def write_run_artifacts(result, records, *, category_md: str, failure_md: str) -> Path:
    """Write history record + category/failure reports; return the history path.
    Same (versions, config) overwrites its own record; new versions are kept."""
    for sub in ("benchmark_history", "category_reports", "failure_reports", "plots"):
        (ANALYSIS_DIR / sub).mkdir(parents=True, exist_ok=True)
    slug = run_slug(result)
    hist_path = ANALYSIS_DIR / "benchmark_history" / f"{slug}.json"
    hist_path.write_text(json.dumps(build_history_record(result, records), indent=2), encoding="utf-8")
    (ANALYSIS_DIR / "category_reports" / f"{slug}.md").write_text(category_md, encoding="utf-8")
    (ANALYSIS_DIR / "failure_reports" / f"{slug}.md").write_text(failure_md, encoding="utf-8")
    return hist_path
