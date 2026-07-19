# Roadmap

Done:

- [x] Memory track: three arms (vector / vector+filter / typedmem) + ablation + metrics
- [x] Reproducible runner (deterministic, records config + seed, keeps per-query results)
- [x] Committed results artifact (`memory/results/`)

Memory track, separated by concern (v0 is a demonstration, not a definitive benchmark):

1. **Dataset expansion** — 33 hand-labeled tasks across 9 categories so far (added long-history, contradictions, cross-session); grow toward 100 → 250 → 500; real-embedder runs; held-out labels.
2. **Router improvement** — fix `what is → fact` over-filtering (the recall regression); justify TypedMem changes with gains on this benchmark.
3. **External baselines** — Mem0 / LangMem / Zep / Letta adapters, after the harness stabilizes.
4. **Real-conversation evaluation** — labeled memories mined from real multi-session transcripts.

Agent track (separate):

- [ ] Fault injection
- [ ] Public leaderboard protocol
