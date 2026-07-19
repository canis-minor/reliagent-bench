"""Router-injectable retrieval pipeline.

Same shape as TypedMem's `TypedRetriever`, but the router is a parameter and an
optional *global fallback* (an unrestricted semantic search merged into the typed
candidates) can be enabled — variant D. Built entirely from TypedMem's public
stage functions, so TypedMem itself is untouched. Records per-query diagnostics
for router metrics.
"""

from __future__ import annotations

from typedmem.embeddings import EmbeddingProvider
from typedmem.retrieval import (
    MemoryVectorizer,
    RetrievalFilters,
    RetrievalIntent,
    apply_filters,
    build_filters,
    rerank,
    resolve_temporal,
    search_candidates,
)
from typedmem.stores.base import MemoryStore

from .baselines import CANDIDATE_K, _single_valued_types
from .routers import Router


class RouterPipelineRetriever:
    def __init__(
        self,
        store: MemoryStore,
        embedder: EmbeddingProvider,
        router: Router,
        *,
        global_fallback: bool = False,
        candidate_k: int = CANDIDATE_K,
        name: str | None = None,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.router = router
        self.global_fallback = global_fallback
        self.candidate_k = candidate_k
        self.name = name or router.name
        self.vz = MemoryVectorizer(embedder)
        self.diagnostics: dict = {}

    def retrieve(self, query: str, top_k: int) -> list[str]:
        route = self.router.route(query)
        types = route.types
        all_mems = list(self.store)

        if types:
            filters = build_filters(
                RetrievalIntent(memory_types=types), workspace=self.store.default_workspace,
            )
        else:
            filters = RetrievalFilters(workspace=self.store.default_workspace)
        pool = apply_filters(all_mems, filters)
        empty_pool = len(pool) == 0

        cands = search_candidates(
            query, pool, embedder=self.embedder, vectorizer=self.vz, top_k=self.candidate_k,
        )
        fallback_used = False
        if self.global_fallback:
            seen = {c.memory.id for c in cands}
            extra = search_candidates(
                query, all_mems, embedder=self.embedder, vectorizer=self.vz, top_k=self.candidate_k,
            )
            new = [c for c in extra if c.memory.id not in seen]
            if new:
                fallback_used = True
            cands = cands + new

        resolved = resolve_temporal(
            [c.memory for c in cands], collapse_types=_single_valued_types(self.store),
        )
        keep = {m.id for m in resolved}
        cands = [c for c in cands if c.memory.id in keep]
        ranked = rerank(cands, intent=RetrievalIntent(memory_types=types))
        result = [rm.memory.id for rm in ranked[:top_k]]

        self.diagnostics = {
            "predicted_types": list(types),
            "num_searched_types": len(types),   # 0 == searched all types
            "confidence": route.confidence,
            "empty_pool": empty_pool,
            "fallback_used": fallback_used,
            "used_llm": route.used_llm,
            "empty_result": len(result) == 0,
        }
        return result
