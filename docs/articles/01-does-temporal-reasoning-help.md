# How much does temporal reasoning actually help agent memory — and why didn't a smarter router?

*A benchmark-driven look at what makes agent memory retrieval correct, using
ReliAgent Bench v1.0. All numbers are preliminary: 104 synthetic tasks, a
deterministic hashing embedder, k=5, seed=0. The point is the method and the
direction of the results, not the absolute scores.*

---

## The bug you can't see in a demo

Ask an agent "What kind of company do I want to work at?" It answers "startups."
Correct — in January. It's now July, and three weeks ago you told it you've soured
on startups and want a large, stable company. The agent's memory still returns
the January note, because that note is a perfect *semantic* match for your
question. It is also *wrong*.

This is the failure mode that matters for long-running agents, and it's invisible
in a one-shot demo. Most memory benchmarks measure semantic similarity — can the
system find text related to the query? The harder question is **correctness under
change**: as memories accumulate and the world moves, does the system return the
one that is *currently* true?

We built a small, frozen benchmark to measure exactly that, and used it to decide
what to build. The results were not what we expected — and the most useful ones
were the features the benchmark told us *not* to build.

## The setup, briefly

**ReliAgent Bench v1.0** is 104 hand-authored tasks across 12 categories
(preference evolution, goal evolution, contradictions, long histories,
cross-session memory, entity ambiguity, status transitions, and more). Each task
is a tiny labeled world: a set of memories, a query, and ground-truth labels for
which memory is *current* and which are *stale* (superseded).

We compare three retrievers behind one interface, `retrieve(query, top_k)`:

- **vector** — embed the query, return the top-k most similar memories. No notion
  of "current."
- **vector + typed filter** — first predict the memory type the query is about
  (a goal? a preference?) and search only that type, then embed.
- **TypedMem** — the full pipeline: type routing → filter → vector search →
  **temporal resolution** (drop superseded memories) → rerank.

Same tasks, same embedder, same top-k, same evaluator for all three. The headline
metrics are **stale-rate** (how often a superseded memory is surfaced — lower is
better) and **current-state accuracy** (is the top result a currently-correct
memory — higher is better).

## Finding 1: temporal reasoning is the whole game

| System | Recall@5 | Stale-rate ↓ | Current-state ↑ |
|---|---:|---:|---:|
| vector | **0.99** | 0.36 | 0.38 |
| vector + typed filter | 0.79 | 0.28 | 0.32 |
| TypedMem | 0.79 | **0.00** | **0.77** |

Vector-only retrieval has near-perfect recall — it finds the relevant memory
almost every time. But it surfaces a *stale* memory 36% of the time and gets the
current answer first only 38% of the time. It has no way to know that "startups"
was superseded by "large companies."

TypedMem drives stale retrieval to **zero** and roughly doubles current-state
accuracy. The mechanism responsible is temporal resolution: it drops any memory
that has been superseded before ranking. That's the win — and it's a specific,
simple mechanism, not "typed memory" in some general sense.

A system-agnostic failure heatmap (labels computed from outputs alone, so they'd
apply to any memory system, including black boxes) makes the trade concrete:

| System | stale | missed | entity | mis-ranked | total failures |
|---|---:|---:|---:|---:|---:|
| vector | 85 | 0 | 1 | 2 | 88 |
| vector + filter | 64 | 21 | 1 | 2 | 88 |
| TypedMem | **0** | 21 | 1 | 2 | **24** |

Vector *never misses* but is drowning in stale results. TypedMem trades 85 stale
retrievals for zero, cutting total failures from 88 to 24.

## Finding 2: the surprise — typed filtering *alone* makes things worse

Look at the middle row again. Adding a typed filter *without* the resolver is
**strictly worse than either extreme**: it still surfaces stale memories (64 —
no resolver to stop them) *and* it newly **misses** 21 memories (the filter
removed them). Same total failures as plain vector, but now split across two
failure modes.

This falsified one of our hypotheses. We assumed "search only the right memory
type" was an obvious precision win. On this benchmark it isn't — it's the
resolver, not the type filter, that earns its place. The filter is a liability we
have to work around.

Where does the filter go wrong? Almost always the same way: a query like *"What
is the user focused on this quarter?"* reads, to a keyword router, as a `fact`
question ("what is..."). So it filters to facts and deletes the goal memories —
and the pipeline returns nothing. On our `implicit_decision` category, this is
catastrophic: **plain vector scores 1.00, TypedMem scores 0.00.** The "dumber"
system wins outright, because the smarter one talked itself out of the answer.

## Finding 3: so we went hunting for a better router

If routing is the problem — and it is; **88% of TypedMem's remaining failures are
routing** — the obvious move is a better router. We ran a controlled experiment
over six routing strategies on a held-out evaluation split, measuring each one's
gap to an **Oracle** router (one that always routes to the correct type):

| Router | Current-state gap to Oracle ↓ |
|---|---:|
| A — hard rule (current) | +0.19 |
| C — soft top-N (predict several types) | +0.19 |
| B — no router at all | **+0.00** |
| D — rule + small global fallback | **+0.00** |

Two more hypotheses fell here.

**Soft routing doesn't help.** Predicting the top-2 or top-3 types instead of one
sounds like it should recover the misses. It doesn't (+0.19, same as hard
routing) — because the router isn't *unsure*, it's *confidently wrong*. It is
certain "What is..." means `fact`, and taking more of its confident-but-wrong
guesses doesn't add `goal`.

**A trivial fallback matches the Oracle.** Variant D keeps the typed search but
adds a small unrestricted semantic search alongside it and merges the two. That
one change closes the gap to the Oracle to **+0.00** — identical to removing the
router entirely. A three-line safety net beats the clever options.

## Why didn't we reach for an LLM router?

Because the benchmark said we didn't need one. The whole justification for an LLM
router is that routing is hard and rules are brittle. That's true — rules *are*
brittle here. But the Oracle router (perfect routing) is only +0.00 ahead of a
dumb global fallback. There is no headroom for an LLM router to claim on this
benchmark; it would add latency, cost, and a network dependency to buy nothing
measurable.

So we **didn't build it.** That is the most important outcome of this cycle: the
benchmark stopped a plausible, expensive feature before we wrote it. It also
stopped soft routing, and it demoted typed filtering from "obvious good idea" to
"liability we route around." Three features prevented, each with a number
attached.

We re-checked all of this as the benchmark grew from 42 → 82 → 104 tasks. The
conclusions held at every size; growth *sharpened* the routing finding (the
router's share of failures rose from 67% → 88% as we added harder cases) rather
than overturning it.

## What this doesn't prove

Being honest about the ceiling of these results:

- The data is **synthetic and hand-authored** — short, clean tasks, not mined
  from real conversations. Real memory is noisier and more paraphrased.
- The embedder is a **deliberately weak** zero-dependency hash, chosen for
  determinism. A strong embedder could move recall and ranking numbers a lot, and
  might shrink the recall cost of filtering.
- It's **104 tasks, one seed, one k.** These are directional results, not
  significance tests.
- We've only compared **internal baselines.** The interesting next question is
  where LLM-summarizing memory systems (Mem0, LangMem, Zep) land on this same
  heatmap — do they avoid stale retrieval, or do they hallucinate a merged
  answer? The benchmark is built to answer that; those runs are pending.

None of this is "TypedMem beats everything." The claim is narrower and, I think,
more useful: **on memory that changes over time, temporal resolution is the
mechanism that matters, typed filtering is not a free win, and a smarter router
is not currently justified — and here is a reproducible benchmark that says so.**

## Reproduce it

```bash
pip install -e .
python -m reliagent_bench.memory --compare  --k 5 --seed 0   # the tables above
python -m reliagent_bench.memory --validate --k 5 --seed 0   # the router gap + stability
```

Deterministic (pure-hash embedder, fixed seed); committed outputs live in the
repo. The full methodology is in [`../benchmark.md`](../benchmark.md); the
first-cycle research notes, including every hypothesis and open question, are in
[`../research-notes.md`](../research-notes.md).

## The bigger bet

The goal was never to win a leaderboard. It was to make architectural decisions
about agent memory the way we make them about the rest of a system: with a
reproducible test that can *change our minds*. In one cycle this benchmark
confirmed two ideas, killed three, and pointed at the next open question. If it
keeps doing that — for TypedMem and for the memory systems we compare it against —
it will have earned its place.
