"""Markdown reporting: comparison table, per-category, and failure examples."""

from __future__ import annotations

from .runner import BenchmarkResult

# Columns shown in the headline comparison (label, metric key, higher-is-better).
_COLUMNS = [
    ("Recall@k", "recall_at_k", True),
    ("Prec@k", "precision_at_k", True),
    ("MRR", "mrr", True),
    ("NDCG", "ndcg_at_k", True),
    ("Wrong-rate", "wrong_memory_rate", False),
    ("Stale-rate", "stale_memory_rate", False),
    ("Cur-state", "current_state_accuracy", True),
]


def _fmt(v: float | None) -> str:
    return "  -  " if v is None else f"{v:6.2f}"


def _table(systems: list[str], rows: dict[str, dict[str, float]]) -> list[str]:
    header = "| System | " + " | ".join(label for label, _, _ in _COLUMNS) + " |"
    sep = "|" + "---|" * (len(_COLUMNS) + 1)
    lines = [header, sep]
    for sys in systems:
        m = rows.get(sys, {})
        cells = " | ".join(_fmt(m.get(key)) for _, key, _ in _COLUMNS)
        lines.append(f"| {sys} | {cells} |")
    return lines


def render_report(result: BenchmarkResult, *, max_failures: int = 8) -> str:
    c = result.config
    systems = c.systems
    out: list[str] = []
    out.append(f"# Memory Retrieval Benchmark — {c.dataset}")
    out.append("")
    out.append(
        f"- tasks: **{c.num_tasks}**  ·  k: **{c.k}**  ·  seed: **{c.seed}**  "
        f"·  embedder: `{c.embedder_id}`  ·  typedmem: `{c.typedmem_version}`"
    )
    out.append("")
    out.append("## Overall")
    out.append("")
    out.extend(_table(systems, result.overall))
    out.append("")
    out.append("> Wrong-rate and Stale-rate are lower-is-better; all others higher-is-better.")

    out.append("")
    out.append("## Per category (Recall@k / Stale-rate / Cur-state)")
    out.append("")
    cat_header = "| Category | " + " | ".join(systems) + " |"
    out.append(cat_header)
    out.append("|" + "---|" * (len(systems) + 1))
    for category in sorted(result.per_category):
        cells = []
        for sys in systems:
            m = result.per_category[category].get(sys, {})
            cells.append(
                f"{m.get('recall_at_k', 0):.2f}/"
                f"{m.get('stale_memory_rate', 0):.2f}/"
                f"{m.get('current_state_accuracy', 0):.2f}"
            )
        out.append(f"| {category} | " + " | ".join(cells) + " |")

    out.append("")
    out.extend(_failure_section(result, max_failures))
    return "\n".join(out)


def _failure_section(result: BenchmarkResult, max_failures: int) -> list[str]:
    """Tasks where the last system (typically 'full'/'typedmem') retrieved a
    stale memory or missed the current one at rank 1."""
    if not result.config.systems:
        return []
    target = result.config.systems[-1]
    failures = [
        q for q in result.per_query
        if q.system == target
        and (q.metrics.get("current_state_accuracy", 1.0) < 1.0
             or q.metrics.get("stale_memory_rate", 0.0) > 0.0)
    ]
    lines = [f"## Failure examples — `{target}` ({len(failures)} total)", ""]
    if not failures:
        lines.append("_None — the target system got the current state right on every task._")
        return lines
    for q in failures[:max_failures]:
        lines.append(f"- **{q.task_id}** ({q.category}) — “{q.query}”")
        lines.append(
            f"  - retrieved: `{q.retrieved_ids}`  ·  "
            f"cur-state={q.metrics.get('current_state_accuracy', 0):.0f}  ·  "
            f"stale-rate={q.metrics.get('stale_memory_rate', 0):.2f}"
        )
    if len(failures) > max_failures:
        lines.append(f"- … and {len(failures) - max_failures} more")
    return lines
