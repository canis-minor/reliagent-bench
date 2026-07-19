# Annotation Guidelines (ReliAgent Bench v1.0)

How tasks are labeled, so a third party can extend the benchmark consistently.

## Task shape (JSONL, one task per line)

```json
{
  "id": "pref-01",
  "category": "preference_evolution",
  "query": "What kind of company does the user prefer to work at now?",
  "memories": [
    {"id": "m1", "type": "preference", "subject": "career_pref",
     "content": "I prefer working at early-stage startups.",
     "timestamp": "2026-01-15", "superseded_by": "m2"},
    {"id": "m2", "type": "preference", "subject": "career_pref",
     "content": "I now prefer working at large mature companies.",
     "timestamp": "2026-07-10"}
  ],
  "relevant_ids": ["m2"],
  "stale_ids": ["m1"]
}
```

Optional fields: `expected_entity` (entity tasks), `difficulty`
(easy/medium/hard; derived if omitted), `requires_{temporal,entity,conflict}_resolution`,
`description`.

## Labeling rules

- **Current state = the answer.** The memory that is true *as of now* — the
  latest, non-superseded memory for the queried subject — goes in `relevant_ids`.
- **Superseded memories are stale.** Every earlier version goes in `stale_ids`
  **and** carries `superseded_by` pointing at the memory that replaces it. The
  resolver uses `superseded_by`; the labels encode ground truth.
- **Distractors are neither.** Memories that are simply unrelated (common in
  `long_history_retrieval`) are omitted from both lists — they count against
  precision if retrieved, but are not "stale".
- **Multi-type answers.** For `mixed_type`, list every memory a correct answer
  must include in `relevant_ids`; the union of their `type`s is what perfect
  routing must search.
- **Entities.** For `entity_disambiguation`, give each entity a distinct
  `subject` and set `expected_entity` to the correct one.
- **Timestamps** are ISO dates; later timestamps are more recent. Keep the
  current answer clearly newer than the stale one.

## Acceptable retrieval

A task is answered correctly when the **top-1** result is a `relevant` memory and
**no `stale` memory** appears in the top-k. Current-State Accuracy and
Stale-Memory Rate encode exactly this.

## Quality bar

- Every task must introduce a *genuine* retrieval challenge — no trivial
  variants of existing tasks.
- Content should share enough tokens with the query that a reasonable embedder
  can surface it, while the stale memory is also plausibly similar (so vector-only
  retrieval is genuinely tempted by the wrong answer).
- Prefer realistic, concrete content over abstract placeholders.

## Adding tasks (post-freeze)

v1.0 is frozen. New tasks go into a **new dataset version** (bump
`DATASET_VERSION`, regenerate `FROZEN_MANIFEST.json`), never by editing v1.0
tasks in place. The freeze test enforces this.
