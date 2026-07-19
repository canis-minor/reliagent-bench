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

# Bump when the dataset's shape or contents change materially. Recorded in the
# benchmark history so results can be compared across dataset versions.
# FROZEN at 1.0 — see datasets/FROZEN_MANIFEST.json and docs/benchmark.md.
# Future changes create a new version rather than modifying v1.0.
DATASET_VERSION = "1.0"

_TEMPORAL_CATEGORIES = {
    "preference_evolution", "goal_evolution", "temporal_updates",
    "status_tracking", "contradictions", "cross_session",
}


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

    # v1.1 structured metadata. Any field left None is derived from task shape
    # (see ``metadata``), so every task has full metadata whether or not the
    # JSONL spells it out.
    difficulty: str | None = None
    required_capabilities: list[str] = field(default_factory=list)
    expected_memory_type: str | None = None
    requires_temporal_resolution: bool | None = None
    requires_entity_resolution: bool | None = None
    requires_conflict_resolution: bool | None = None
    description: str = ""

    @property
    def relevant(self) -> set[str]:
        return set(self.relevant_ids)

    @property
    def stale(self) -> set[str]:
        return set(self.stale_ids)

    def _distractors(self) -> int:
        return max(0, len(self.memories) - len(self.relevant) - len(self.stale))

    def eff_requires_temporal(self) -> bool:
        if self.requires_temporal_resolution is not None:
            return self.requires_temporal_resolution
        return bool(self.stale_ids) or any(m.get("superseded_by") for m in self.memories)

    def eff_requires_entity(self) -> bool:
        if self.requires_entity_resolution is not None:
            return self.requires_entity_resolution
        return self.expected_entity is not None

    def eff_requires_conflict(self) -> bool:
        if self.requires_conflict_resolution is not None:
            return self.requires_conflict_resolution
        return self.category == "contradictions"

    def relevant_types(self) -> list[str]:
        """Distinct memory types across the relevant memories (in order). A
        mixed-type task has more than one; perfect routing must cover them all."""
        seen: list[str] = []
        for m in self.memories:
            if m["id"] in self.relevant and m["type"] not in seen:
                seen.append(m["type"])
        return seen

    def eff_expected_memory_type(self) -> str | None:
        if self.expected_memory_type:
            return self.expected_memory_type
        types = self.relevant_types()
        return types[0] if types else None

    def eff_difficulty(self) -> str:
        if self.difficulty:
            return self.difficulty
        if len(self.memories) >= 6 or self.category in ("long_history_retrieval", "cross_session"):
            return "hard"
        if self.eff_requires_temporal() or self.eff_requires_entity() or self._distractors() > 0:
            return "medium"
        return "easy"

    def eff_capabilities(self) -> list[str]:
        if self.required_capabilities:
            return self.required_capabilities
        caps = [self.category]
        if self.eff_requires_temporal():
            caps.append("temporal")
        if self.eff_requires_entity():
            caps.append("entity")
        if self.eff_requires_conflict():
            caps.append("conflict")
        return caps

    def metadata(self) -> dict:
        """Full structured metadata (explicit fields, else derived)."""
        return {
            "id": self.id,
            "category": self.category,
            "difficulty": self.eff_difficulty(),
            "required_capabilities": self.eff_capabilities(),
            "expected_memory_type": self.eff_expected_memory_type(),
            "requires_temporal_resolution": self.eff_requires_temporal(),
            "requires_entity_resolution": self.eff_requires_entity(),
            "requires_conflict_resolution": self.eff_requires_conflict(),
            "description": self.description,
        }


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


FROZEN_MANIFEST = DATASETS_DIR / "FROZEN_MANIFEST.json"


def dataset_fingerprint(tasks: list[MemoryTask] | None = None) -> dict:
    """A version + shape + content fingerprint of the frozen dataset. The
    committed FROZEN_MANIFEST.json must match this; the freeze test enforces it,
    so any accidental change to v1.0 is caught."""
    import hashlib
    from collections import Counter

    tasks = tasks if tasks is not None else load_tasks()
    ordered = sorted(tasks, key=lambda t: t.id)
    canon = json.dumps(
        [
            {"id": t.id, "category": t.category, "query": t.query,
             "memories": t.memories, "relevant_ids": t.relevant_ids,
             "stale_ids": t.stale_ids, "expected_entity": t.expected_entity}
            for t in ordered
        ],
        sort_keys=True, ensure_ascii=False,
    )
    return {
        "dataset_version": DATASET_VERSION,
        "num_tasks": len(tasks),
        "categories": dict(sorted(Counter(t.category for t in tasks).items())),
        "task_ids": [t.id for t in ordered],
        "content_sha256": hashlib.sha256(canon.encode("utf-8")).hexdigest(),
    }
