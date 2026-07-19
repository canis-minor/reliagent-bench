"""Declarative memory-retrieval tasks.

A task is a small, hand-labeled world: a list of memory records, a query, and
the ground-truth ids that *should* / *should not* be retrieved. Tasks are stored
as JSONL (one task per line) so they are diff-friendly and versionable.

``build_store`` materializes a task into a fresh in-memory TypedMem store using
the library's PUBLIC API only — each record is inserted verbatim via a ``create``
Transition so the labeled timeline (timestamps, supersession) is preserved
exactly, with no conflict resolution rewriting it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from typedmem import InMemoryStore, Memory, Transition

DATASETS_DIR = Path(__file__).resolve().parent / "datasets"
DEFAULT_DATASET = DATASETS_DIR / "seed.jsonl"


@dataclass
class MemoryTask:
    id: str
    category: str
    query: str
    memories: list[dict]
    relevant_ids: list[str]
    stale_ids: list[str] = field(default_factory=list)
    expected_entity: str | None = None
    top_k: int | None = None
    as_of: str | None = None
    notes: str = ""

    @property
    def relevant(self) -> set[str]:
        return set(self.relevant_ids)

    @property
    def stale(self) -> set[str]:
        return set(self.stale_ids)


def _parse_ts(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def load_tasks(path: str | Path = DEFAULT_DATASET) -> list[MemoryTask]:
    """Load tasks from a JSONL file (blank lines and ``# ...`` lines ignored)."""
    tasks: list[MemoryTask] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tasks.append(MemoryTask(**json.loads(line)))
    return tasks


def build_store(task: MemoryTask, *, workspace: str = "default") -> InMemoryStore:
    """Materialize a task's memories into a fresh store, verbatim."""
    store = InMemoryStore()
    for spec in task.memories:
        m = Memory(
            type=spec["type"],
            content=spec["content"],
            subject=spec.get("subject"),
            status=spec.get("status"),
            id=spec["id"],
            workspace=workspace,
            superseded_by=spec.get("superseded_by"),
            timestamp=_parse_ts(spec.get("timestamp")),
        )
        store.apply_transition(Transition(action="create", memory=m, actor="system"))
    return store


def subject_map(task: MemoryTask) -> dict[str, str | None]:
    """id → subject, for entity-resolution scoring."""
    return {spec["id"]: spec.get("subject") for spec in task.memories}
