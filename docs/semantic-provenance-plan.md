# Evaluating Semantic Provenance Representations

**Track:** C — Semantic provenance
**Status:** Research design (no cases yet)
**Relation to the frozen memory track:** additive; Track A (memory retrieval, v1.0)
is untouched.

---

## Why this lives in the benchmark, not in a system

Semantic-provenance systems claim to localize agent failures that operational traces
miss — by recording not *what executed* but *what the agent believed*, why the belief
changed, and which decisions depended on it. [StateGraph](https://github.com/canis-minor/stategraph)
is the first such system, and its v0.1 experiment showed the idea can work.

But a system cannot be the court that judges itself. If every project ships "its own
benchmark," the results are unpersuasive. This plan therefore evaluates the *class* of
representation independently. **StateGraph is one implementation under test, not the
assumed winner.** A simpler representation that does equally well is a success of this
track, not a failure.

The question is no longer *"can a semantic graph represent agent state?"* (StateGraph
answered that). It is:

> Is a semantic-provenance representation **necessary**, **sufficient**, and
> **reproducible** — and does it **help** more than an operational trace?

---

## What is under evaluation

A *semantic-provenance representation* is any scheme that records, for one agent run,
the evidence it observed, the claims it held, how contradictions were handled, and
which decisions each claim justified. The **candidate ontology** — the reference point,
as implemented by StateGraph v0.1 — has five node types:

`Evidence · Claim · Conflict · Decision · Transition`

This plan treats those five as a *hypothesis about the right vocabulary*, and tests it
against simpler and richer alternatives. No node type is privileged by assumption.

---

## Research questions

### RQ1 — Sufficiency
Can the candidate ontology express the targeted class of semantic failures?
- Which failures cannot be represented at all?
- Which require node types not in the set?
- Which node types are never exercised by any case?

### RQ2 — Necessity
Are all five node types actually needed? Evaluate alternative ontologies on the same
cases:

| Ontology | Shape | Bet |
|---|---|---|
| **O1** | Evidence → Claim → Decision | conflict/transition are unnecessary ceremony |
| **O2** | Evidence → Claim → Decision, **conflict derived** | conflict is computable, not primitive |
| **O3** | Evidence → **State** → Decision | one opaque "state" blob suffices |
| **O4** | Evidence → Claim → Decision, **transitions as edges** | transition is an edge, not a node |

If a simpler ontology localizes the same failures, it wins (Outcome D). The metric that
matters is *failures localized per node type*, not node count.

### RQ3 — Reproducibility
Can two annotators independently build similar graphs for the same case? Measure
inter-annotator agreement on nodes, edges, conflicts, and decision justifications. The
goal is to show the ontology is *shared and teachable*, not merely intuitive to its
author.

### RQ4 — Utility vs. operational trace
Does the semantic representation actually improve debugging over an operational trace
of the same run? Present each failure case in two forms — an **operational trace**
(the Track-B / [AgentTrace](https://github.com/canis-minor/agenttrace) baseline) and a
**semantic graph** — and measure, for each, diagnosis accuracy, localization time,
confidence, and records inspected. This is the load-bearing experiment: without it,
semantic provenance is unfalsified.

---

## Benchmark design

**Target: 30 cases.** Each case is representation-agnostic — it does not assume any
particular ontology, so O1–O4 and StateGraph are all scored on the same ground truth.

Categories: `contradiction · superseded_information · state_evolution ·
decision_justification · cascading_dependency · mixed_semantic_failure`.

Each case contains:

```text
Conversation → Evidence timeline → Expected current state → Expected decision
→ Expected explanation → Reference semantic graph (+ known failure point & category)
```

The reference graph is a *target*, not the definition of correctness: correctness is
the expected state / decision / explanation, which any ontology may try to recover.

---

## Annotation specification

An annotation guide is written **before** the benchmark is expanded. For every node
type it must give: definition, inclusion criteria, exclusion criteria, positive and
negative examples, and edge cases. Success condition: a second researcher can annotate
a case *without consulting the original author* and land within the agreement
thresholds (RQ3).

---

## Metrics

- **Ontology complexity** — node types; avg nodes/edges per case.
- **Representation quality** — localization accuracy; explanation completeness; semantic correctness.
- **Reproducibility** — inter-annotator agreement; disagreement categories.
- **Human utility** — debugging time; confidence; inspection effort (vs. the operational baseline).

---

## Non-goals (this phase)

Methodology, not implementation. Explicitly excluded until the representation is
validated: visualization, HTML viewer, CLI, automatic graph extraction, the
AgentTrace→StateGraph bridge, and LLM-assisted annotation. The benchmark also privileges
no system — it evaluates representations, StateGraph among them.

---

## Possible outcomes

- **A** — the candidate ontology is validated with minor refinement.
- **B** — some node types are unnecessary and get removed.
- **C** — additional node types are required.
- **D** — a substantially simpler ontology does equally well.

**D is a successful scientific result**, not a failure: fewer concepts explaining the
same failures is exactly the direction a representation should move.

---

## Exit criteria

Complete when these are answered by **evidence, not intuition**:

1. Which semantic objects are necessary?
2. Which are sufficient?
3. Can different people build similar graphs?
4. Does semantic provenance improve debugging over an operational trace?

Only then is automatic extraction (AgentTrace → candidate StateGraph evidence) worth
investigating — and it enters as an implementation convenience, not part of the claim.
