"""External memory-system adapters.

Each adapter maps the benchmark's `retrieve(query, top_k) -> [memory_id]`
interface onto a third-party memory system. Per task the adapter gets a fresh
instance, ingests that task's memories (tagging each with its benchmark id), and
answers the query. TypedMem and the benchmark are untouched — only the adapter
varies.

⚠️ EXPERIMENTAL / UNVERIFIED. These adapters are written against the systems'
documented public APIs but are **not** exercised in CI (the systems need their
packages plus live services / API keys). Verify against your installed version
before trusting results. `available()` gates each adapter on import + minimal
config, so a missing system is simply skipped rather than breaking a run.
"""

from __future__ import annotations

import os
from typing import Protocol

from .dataset import MemoryTask

_UID = "reliagent_bench"


class ExternalRetriever(Protocol):
    name: str
    def ingest(self, task: MemoryTask) -> None: ...
    def retrieve(self, query: str, top_k: int) -> list[str]: ...


def _memory_text(spec: dict) -> str:
    return spec["content"]


class Mem0Retriever:
    """Adapter for Mem0 (`pip install mem0ai`). Needs an embedder/LLM key (e.g.
    OPENAI_API_KEY) and a vector store; uses Mem0's defaults.

    Validated against the **mem0ai 2.0.12** API surface (calls verified by
    introspection; not run end-to-end here — that needs a live key). Key details
    for a fair benchmark run:
    - ``infer=False`` on ``add`` stores each benchmark memory **verbatim** (1:1);
      the default ``infer=True`` would run an LLM to extract/rewrite facts,
      breaking the id mapping and changing what is being measured.
    - ``search`` takes ``top_k`` (not ``limit``) and scopes via
      ``filters={"user_id": ...}`` (not a bare ``user_id=`` kwarg).
    - custom metadata round-trips under ``result["metadata"]``, so the benchmark
      id comes back as ``result["metadata"]["mid"]``."""

    name = "mem0"

    def __init__(self) -> None:
        from mem0 import Memory
        self._m = Memory()

    @staticmethod
    def available() -> bool:
        try:
            import mem0  # noqa: F401
        except Exception:
            return False
        return bool(os.getenv("OPENAI_API_KEY"))

    def ingest(self, task: MemoryTask) -> None:
        for spec in task.memories:
            # infer=False → store verbatim; metadata carries our benchmark id.
            self._m.add(_memory_text(spec), user_id=_UID,
                        metadata={"mid": spec["id"]}, infer=False)

    def retrieve(self, query: str, top_k: int) -> list[str]:
        res = self._m.search(query, top_k=top_k, filters={"user_id": _UID})
        items = res.get("results", []) if isinstance(res, dict) else (res or [])
        ids: list[str] = []
        for r in items:
            meta = (r.get("metadata") or {}) if isinstance(r, dict) else {}
            if meta.get("mid"):
                ids.append(meta["mid"])
        return ids[:top_k]


class LangMemRetriever:
    """Adapter for LangMem (`pip install langmem`). Needs an LLM/embeddings
    backend. LangMem's retrieval surface varies by version — adapt the two marked
    calls to your installed API."""

    name = "langmem"

    def __init__(self) -> None:
        from langmem import create_memory_store_manager  # API varies by version
        self._store = create_memory_store_manager()  # verify signature for your version
        self._items: dict[str, str] = {}

    @staticmethod
    def available() -> bool:
        try:
            import langmem  # noqa: F401
        except Exception:
            return False
        return bool(os.getenv("OPENAI_API_KEY"))

    def ingest(self, task: MemoryTask) -> None:
        for spec in task.memories:
            self._items[spec["id"]] = _memory_text(spec)
            # verify: how your langmem version records a memory + metadata id
            self._store.put(spec["id"], _memory_text(spec))

    def retrieve(self, query: str, top_k: int) -> list[str]:
        # verify: how your langmem version searches; must return benchmark ids
        hits = self._store.search(query, limit=top_k)
        return [h["id"] if isinstance(h, dict) else h for h in hits][:top_k]


class ZepRetriever:
    """Adapter for Zep (`pip install zep-cloud`). Needs ZEP_API_KEY (Zep Cloud)
    or a self-hosted Zep server URL."""

    name = "zep"

    def __init__(self) -> None:
        from zep_cloud.client import Zep
        self._client = Zep(api_key=os.environ["ZEP_API_KEY"])

    @staticmethod
    def available() -> bool:
        try:
            import zep_cloud  # noqa: F401
        except Exception:
            return False
        return bool(os.getenv("ZEP_API_KEY"))

    def ingest(self, task: MemoryTask) -> None:
        self._session = f"{_UID}-{task.id}"
        # verify: your Zep version's graph/memory add API; store id in metadata
        for spec in task.memories:
            self._client.memory.add(
                session_id=self._session,
                messages=[{"role": "user", "content": _memory_text(spec), "metadata": {"mid": spec["id"]}}],
            )

    def retrieve(self, query: str, top_k: int) -> list[str]:
        res = self._client.memory.search_sessions(text=query, session_ids=[self._session], limit=top_k)
        ids: list[str] = []
        for r in getattr(res, "results", res) or []:
            meta = getattr(r, "metadata", {}) or {}
            if meta.get("mid"):
                ids.append(meta["mid"])
        return ids[:top_k]


_EXTERNAL = [Mem0Retriever, LangMemRetriever, ZepRetriever]


def _external_prep(factory):
    def build(task: MemoryTask, embedder):  # embedder unused: external systems embed internally
        inst = factory()
        inst.ingest(task)
        return inst.retrieve
    return build


def available_external_names() -> list[str]:
    return [f.name for f in _EXTERNAL if _safe_available(f)]


def _safe_available(factory) -> bool:
    try:
        return bool(factory.available())
    except Exception:
        return False


def available_systems(*, include_external: bool = True):
    """Built-in systems, plus any external adapter whose package + config is
    present. External systems are skipped (not faked) when unavailable."""
    from .cross_system import builtin_systems

    systems = builtin_systems()
    if include_external:
        for factory in _EXTERNAL:
            if _safe_available(factory):
                systems.append((factory.name, _external_prep(factory)))
    return systems
