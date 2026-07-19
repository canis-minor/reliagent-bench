# Cross-system comparison (ReliAgent Bench v1.0)

- systems: **vector, vector_filter, typedmem** · tasks: **104** · k=5 · seed=0 · embedder `hashing:dim=1024;ngram=2`
- benchmark 1.0 · dataset 1.0 · typedmem 0.8.0 · python 3.13.1
- external memory packages: none installed

### Overall

| System | Recall | Prec | MRR | NDCG | Stale | Cur-state |
|---|---|---|---|---|---|---|
| vector | 0.99 | 0.48 | 0.68 | 0.76 | 0.36 | 0.38 |
| vector_filter | 0.79 | 0.40 | 0.55 | 0.61 | 0.28 | 0.32 |
| typedmem | 0.79 | 0.66 | 0.78 | 0.78 | 0.00 | 0.77 |

### Category leaderboard (current_state_accuracy)

| Category | vector | vector_filter | typedmem |
|---|---|---|---|
| contradictions | 0.00 | 0.00 | 1.00 |
| cross_session | 0.40 | 0.40 | 1.00 |
| decision_retrieval | 0.25 | 0.17 | 0.67 |
| entity_disambiguation | 0.92 | 0.92 | 0.92 |
| goal_evolution | 0.30 | 0.10 | 0.60 |
| implicit_decision | 1.00 | 0.00 | 0.00 |
| implicit_goal | 0.25 | 0.25 | 0.25 |
| long_history_retrieval | 0.00 | 0.00 | 1.00 |
| mixed_type | 1.00 | 1.00 | 1.00 |
| preference_evolution | 0.64 | 0.64 | 1.00 |
| status_tracking | 0.09 | 0.00 | 0.18 |
| temporal_updates | 0.22 | 0.22 | 1.00 |

### Failure heatmap (system-agnostic; counts, lower is better)

| System | stale | missed | entity | mis_ranked | total |
|---|---|---|---|---|---|
| vector | 85 | 0 | 1 | 2 | 88 |
| vector_filter | 64 | 21 | 1 | 2 | 88 |
| typedmem | 0 | 21 | 1 | 2 | 24 |

> Failure labels are computed from outputs only (stale surfaced / relevant missed / wrong entity / relevant mis-ranked), so they apply to any system — glass-box or black-box.