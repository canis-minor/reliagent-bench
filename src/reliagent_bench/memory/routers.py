"""Router strategies for the v1.2 router experiment.

A `Router` maps a query to a `RouteResult` (predicted memory types + confidence).
The benchmark pipeline injects one of these and keeps the resolver + ranker fixed,
so only routing varies. TypedMem is NOT modified — the rule router reuses
TypedMem's public `route_query`; the others are composed here. Only after a
router wins on the benchmark should it become a TypedMem default.

Variants (see the design's matrix):
  A `RuleRouter`        — current hard rule router (baseline)
  B `NoRouter`          — no routing (control)
  C `SoftRuleRouter`    — top-N candidate types
  D  RuleRouter + global fallback  (a pipeline flag, not a router)
  E `LLMRouter`         — LLM routing (structured, temp=0, versioned prompt, cached)
  F `HybridRouter`      — rule first, LLM only when the rule is unconfident
  •  `OracleRouter`     — routes to the labeled type; an upper-bound reference
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from typedmem.retrieval import route_query

# Allowed types for LLM routing (built-ins + common profile types).
ALLOWED_TYPES = [
    "fact", "preference", "goal", "decision", "project", "event",
    "status", "observation",
]

ROUTER_PROMPT_VERSION = "v1"
ROUTER_PROMPT = (
    "You are a query router for a typed memory system.\n"
    "Given a user query, predict which memory types are relevant.\n"
    "Allowed types: {allowed}.\n"
    'Respond ONLY with JSON: {{"types": ["..."], "confidence": 0.0-1.0}}.\n'
    "Query: {query}"
)


@dataclass
class RouteResult:
    types: list[str] = field(default_factory=list)  # empty = no type restriction
    confidence: float = 1.0
    method: str = ""
    used_llm: bool = False


class Router(Protocol):
    name: str
    def route(self, query: str) -> RouteResult: ...


class RuleRouter:
    """A — TypedMem's current rule router (hard, single/multi type)."""

    name = "rule"

    def route(self, query: str) -> RouteResult:
        types = route_query(query).memory_types or []
        return RouteResult(types=types, confidence=1.0 if types else 0.0, method="rule")


class NoRouter:
    """B — no routing; the pipeline searches all types (control group)."""

    name = "none"

    def route(self, query: str) -> RouteResult:
        return RouteResult(types=[], confidence=0.0, method="none")


class SoftRuleRouter:
    """C — soft rule router: keep the top-N matched candidate types."""

    def __init__(self, top_n: int = 2) -> None:
        self.top_n = top_n
        self.name = f"soft_top{top_n}"

    def route(self, query: str) -> RouteResult:
        types = (route_query(query).memory_types or [])[: self.top_n]
        return RouteResult(types=types, confidence=1.0 if types else 0.0, method="soft")


class OracleRouter:
    """Upper-bound reference — routes each query to its labeled expected type.
    Needs the dataset's query→types map. NOT a deployable router; it measures the
    ceiling that perfect routing would reach."""

    name = "oracle"

    def __init__(self, query_to_types: dict[str, list[str]]) -> None:
        self._map = query_to_types

    def route(self, query: str) -> RouteResult:
        return RouteResult(types=list(self._map.get(query, [])), confidence=1.0, method="oracle")

    @classmethod
    def from_tasks(cls, tasks) -> "OracleRouter":
        mapping: dict[str, list[str]] = {}
        for t in tasks:
            et = t.eff_expected_memory_type()
            mapping[t.query] = [et] if et else []
        return cls(mapping)


class LLMRouter:
    """E — LLM routing. Structured output, temperature=0 (via the client),
    a versioned prompt, and a response cache for deterministic replay. On a cache
    miss with no client, replay fails loudly (reproducibility guard)."""

    name = "llm"

    def __init__(
        self,
        client=None,
        *,
        cache: dict[str, dict] | None = None,
        prompt_version: str = ROUTER_PROMPT_VERSION,
        allowed_types: list[str] | None = None,
    ) -> None:
        self.client = client
        self.cache = cache if cache is not None else {}
        self.prompt_version = prompt_version
        self.allowed = allowed_types or ALLOWED_TYPES
        self.calls = 0  # live LLM invocations (cost/latency accounting)

    def _key(self, query: str) -> str:
        return f"{self.prompt_version}::{query}"

    def route(self, query: str) -> RouteResult:
        key = self._key(query)
        if key in self.cache:
            data = self.cache[key]
        elif self.client is not None:
            prompt = ROUTER_PROMPT.format(allowed=", ".join(self.allowed), query=query)
            self.calls += 1
            data = self._parse(self.client.complete(prompt))
            self.cache[key] = data
        else:
            raise RuntimeError(
                f"LLMRouter: cache miss for {query!r} and no client for replay"
            )
        types = [t for t in data.get("types", []) if t in self.allowed]
        return RouteResult(
            types=types, confidence=float(data.get("confidence", 1.0)),
            method="llm", used_llm=True,
        )

    @staticmethod
    def _parse(raw: str) -> dict:
        m = re.search(r"\{.*\}", raw or "", re.S)
        if not m:
            return {"types": []}
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return {"types": []}


class HybridRouter:
    """F — rule first; invoke the LLM only when the rule is unconfident
    (no rule matched, i.e. confidence below the threshold)."""

    name = "hybrid"

    def __init__(self, rule: Router, llm: LLMRouter, *, min_confidence: float = 1.0) -> None:
        self.rule = rule
        self.llm = llm
        self.min_confidence = min_confidence
        self.fallbacks = 0

    def route(self, query: str) -> RouteResult:
        r = self.rule.route(query)
        if r.types and r.confidence >= self.min_confidence:
            r.method = "hybrid"
            return r
        self.fallbacks += 1
        out = self.llm.route(query)
        out.method = "hybrid"
        return out


# ── LLM response cache persistence (deterministic replay) ──────────────────
def load_cache(path: str | Path) -> dict[str, dict]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_cache(path: str | Path, cache: dict[str, dict]) -> None:
    Path(path).write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
