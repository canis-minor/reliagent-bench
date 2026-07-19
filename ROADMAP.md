# Roadmap

Done:

- [x] Memory track: three arms (vector / vector+filter / typedmem) + ablation + metrics
- [x] Reproducible runner (deterministic, records config + seed, keeps per-query results)
- [x] Committed results artifact (`memory/results/`)
- [x] Structured per-task metadata + difficulty levels
- [x] Classified failure analysis (router/embedding/temporal/entity/ranking) + stage contribution
- [x] Versioned benchmark history with commit hashes (`analysis/`)
- [x] Router experiment harness: variants A–F + Oracle, injected via public stages (TypedMem unchanged), dev/eval split, router metrics, matrix report

Memory track, separated by concern (v0 is a demonstration, not a definitive benchmark):

1. **Dataset expansion** — 33 hand-labeled tasks across 9 categories so far (added long-history, contradictions, cross-session); grow toward 100 → 250 → 500; real-embedder runs; held-out labels.
2. **Router improvement** — the v1.2 experiment shows **D (rule + global fallback)** recovers the recall the hard router loses while keeping typed precision + zero stale; **B (no router)** matches it, **C (soft top-N)** does not help. Deferred pending ~100 tasks and an E/F (LLM/hybrid) run before adopting a TypedMem default.
3. **External baselines** — Mem0 / LangMem / Zep / Letta adapters, after the harness stabilizes.
4. **Real-conversation evaluation** — labeled memories mined from real multi-session transcripts.

Agent track (separate):

- [ ] Fault injection
- [ ] Public leaderboard protocol
