"""Retrieval adapters (the benchmark "arms").

All three arms call TypedMem's PUBLIC API — nothing is copied out of the library:

* ``VectorRetriever``          — embedding → top-k over ALL memories.
* ``FilteredVectorRetriever``  — typed metadata filters → vector → top-k.
* ``TypedMemRetriever``        — the full public ``TypedRetriever`` pipeline.

``AblationRetriever`` composes the public stage functions with per-stage toggles
so each component's contribution can be measured.

Common interface: ``retrieve(query, top_k) -> list[str]`` (memory ids). A
"system" is a ``(name, factory)`` pair where ``factory(store, embedder)`` builds
an adapter — so every arm is rebound to the same per-task store and embedder.
"""

from __future__ import annotations

from typing import Callable, Protocol

from typedmem import TypedRetriever
from typedmem.embeddings import EmbeddingProvider
from typedmem.retrieval import (
    MemoryVectorizer,
    RetrievalFilters,
    RetrievalIntent,
    apply_filters,
    build_filters,
    rerank,
    resolve_temporal,
    route_query,
    search_candidates,
)
from typedmem.stores.base import MemoryStore


class RetrieverAdapter(Protocol):
    name: str
    def retrieve(self, query: str, top_k: int) -> list[str]: ...


SystemFactory = Callable[[MemoryStore, EmbeddingProvider], RetrieverAdapter]

# Candidate pool for pipelines that filter/resolve before ranking. Kept larger
# than top_k so resolution/ranking has room to work; shared across arms.
CANDIDATE_K = 50


def _single_valued_types(store: MemoryStore) -> set[str]:
    types: set[str] = set()
    for m in store:
        try:
            if store.policy.policy_for(m.type).updatable:
                types.add(m.type)
        except KeyError:
            continue
    return types


class VectorRetriever:
    """Baseline A — vector-only. No filters, no temporal resolution, no rerank."""

    name = "vector"

    def __init__(self, store: MemoryStore, embedder: EmbeddingProvider) -> None:
        self.store = store
        self.embedder = embedder
        self.vz = MemoryVectorizer(embedder)

    def retrieve(self, query: str, top_k: int) -> list[str]:
        cands = search_candidates(
            query, list(self.store), embedder=self.embedder,
            vectorizer=self.vz, top_k=top_k,
        )
        return [c.memory.id for c in cands]


class FilteredVectorRetriever:
    """Baseline B — typed metadata filters, then vector. No temporal resolution."""

    name = "vector_filter"

    def __init__(self, store: MemoryStore, embedder: EmbeddingProvider) -> None:
        self.store = store
        self.embedder = embedder
        self.vz = MemoryVectorizer(embedder)

    def retrieve(self, query: str, top_k: int) -> list[str]:
        intent = route_query(query)
        filters = build_filters(intent, workspace=self.store.default_workspace)
        pool = apply_filters(list(self.store), filters)
        cands = search_candidates(
            query, pool, embedder=self.embedder, vectorizer=self.vz, top_k=top_k,
        )
        return [c.memory.id for c in cands]


class TypedMemRetriever:
    """TypedMem v0 — the full public pipeline (router → filters → vector →
    temporal resolution → rerank)."""

    name = "typedmem"

    def __init__(self, store: MemoryStore, embedder: EmbeddingProvider) -> None:
        self.inner = TypedRetriever(store, embedder=embedder, candidate_k=CANDIDATE_K)

    def retrieve(self, query: str, top_k: int) -> list[str]:
        return [m.id for m in self.inner.retrieve(query, top_k=top_k)]


class AblationRetriever:
    """Configurable pipeline for the ablation study — composes public stage
    functions with per-stage toggles."""

    def __init__(
        self,
        store: MemoryStore,
        embedder: EmbeddingProvider,
        *,
        name: str,
        use_router: bool = True,
        use_filters: bool = True,
        use_resolver: bool = True,
        use_ranker: bool = True,
        candidate_k: int = CANDIDATE_K,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.vz = MemoryVectorizer(embedder)
        self.name = name
        self.use_router = use_router
        self.use_filters = use_filters
        self.use_resolver = use_resolver
        self.use_ranker = use_ranker
        self.candidate_k = candidate_k

    def retrieve(self, query: str, top_k: int) -> list[str]:
        intent = route_query(query) if self.use_router else RetrievalIntent()
        if self.use_filters:
            filters = build_filters(intent, workspace=self.store.default_workspace)
        else:
            filters = RetrievalFilters(workspace=self.store.default_workspace)
        pool = apply_filters(list(self.store), filters)
        cands = search_candidates(
            query, pool, embedder=self.embedder, vectorizer=self.vz, top_k=self.candidate_k,
        )
        if self.use_resolver:
            resolved = resolve_temporal(
                [c.memory for c in cands], collapse_types=_single_valued_types(self.store),
            )
            keep = {m.id for m in resolved}
            cands = [c for c in cands if c.memory.id in keep]
        if self.use_ranker:
            ordered = [r.memory for r in rerank(cands, intent=intent)]
        else:
            ordered = [c.memory for c in cands]
        return [m.id for m in ordered[:top_k]]


# The three primary arms (call these for the headline comparison).
def _vector(store, embedder):        return VectorRetriever(store, embedder)
def _vector_filter(store, embedder): return FilteredVectorRetriever(store, embedder)
def _typedmem(store, embedder):      return TypedMemRetriever(store, embedder)


DEFAULT_SYSTEMS: list[tuple[str, SystemFactory]] = [
    ("vector", _vector),
    ("vector_filter", _vector_filter),
    ("typedmem", _typedmem),
]

# Stage ablation: vector → +filters → +resolver → full.
ABLATION_SYSTEMS: list[tuple[str, SystemFactory]] = [
    ("vector", lambda s, e: AblationRetriever(
        s, e, name="vector", use_router=False, use_filters=False,
        use_resolver=False, use_ranker=False)),
    ("+filters", lambda s, e: AblationRetriever(
        s, e, name="+filters", use_resolver=False, use_ranker=False)),
    ("+resolver", lambda s, e: AblationRetriever(
        s, e, name="+resolver", use_ranker=False)),
    ("full", lambda s, e: AblationRetriever(s, e, name="full")),
]
