# Roadmap

Done:

- [x] Memory track: three arms (vector / vector+filter / typedmem) + ablation + metrics
- [x] Reproducible runner (deterministic, records config + seed, keeps per-query results)
- [x] Committed results artifact (`memory/results/`)
- [x] Structured per-task metadata + difficulty levels
- [x] Classified failure analysis (router/embedding/temporal/entity/ranking) + stage contribution
- [x] Versioned benchmark history with commit hashes (`analysis/`)
- [x] Router experiment harness: variants A–F + Oracle, injected via public stages (TypedMem unchanged), dev/eval split, router metrics, matrix report
- [x] Validation at scale (82 tasks): Oracle Gap, failure distribution, cross-version stability, data-driven decision
- [x] Dataset grown to 82 tasks across 11 categories (added implicit_goal, mixed_type routing-stress)

Memory track, separated by concern (v0 is a demonstration, not a definitive benchmark):

1. **Dataset expansion** — 82 hand-labeled tasks across 11 categories so far; grow toward ~100 → 250 → 500; real-embedder runs; held-out labels.
2. **Router improvement** — v1.2/v1.3 (82 tasks) show **D (rule + global fallback) ≈ Oracle** (current-state gap +0.00); **B (no router)** matches, **C (soft top-N)** does not help. Decision **Case A**: routing is effectively solved by the fallback — **LLM routing (E/F) is NOT justified yet**. Adopting the fallback in TypedMem is the eventual change once re-confirmed nearer 100 tasks.
3. **External baselines** (next active track, per Case A) — Mem0 / LangMem / Zep / Letta adapters on identical dataset / evaluator / metrics / top-k / embedding, after the harness stabilizes.
4. **Real-conversation evaluation** — labeled memories mined from real multi-session transcripts.

Agent track (separate):

- [ ] Fault injection
- [ ] Public leaderboard protocol
