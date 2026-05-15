# Ocean Autonomous Product Intelligence Loop

## Core Idea

Ocean is not a coding agent.

Ocean is an external product intelligence layer that continuously asks:

> “What is the smallest next change that makes this product more valuable to the intended user?”

Ocean orchestrates specialized personas that compete and collaborate to identify the highest-leverage next work.

The system is designed to maximize:

* user value
* learning speed
* implementation efficiency
* strategic coherence
* long-term product quality

The system is NOT designed to maximize:

* feature count
* code volume
* persona wealth
* voting power

The scarce resource is implementation bandwidth and tokens.

---

# System Architecture

## Personas

Each persona represents a competing optimization function inside a software company.

Example personas:

* Moroni → architecture, sequencing, vision
* Q → backend capability and engineering leverage
* Edna → UX, usability, accessibility
* Mario → infrastructure, deployment, operational simplicity
* Tony → testing, telemetry, robustness

The personas SHOULD disagree.

The disagreement is the source of intelligence.

---

# Constitutional Layer vs Evidence Layer

## Constitutional Layer (Stable)

These documents define the identity and doctrine of the product.

They should evolve slowly.

Examples:

* VISION.md
* AUDIENCE.md
* PRODUCT_PRINCIPLES.md
* UX_RULES.md
* DECISIONS.md

Purpose:

* prevent drift
* preserve product identity
* maintain strategic coherence

These are NOT hardcoded truths.
They are durable guidance.

---

## Evidence Layer (Dynamic)

These are continuously changing signals.

Examples:

* user feedback
* telemetry
* competitor research
* support tickets
* analytics
* recent shipped work
* web research
* discovered APIs
* proprietary streams
* peer proposal history

Personas may gather new evidence each round.

New evidence may change priorities.

New evidence does NOT automatically rewrite doctrine.

Doctrine changes require explicit review.

---

# Round Loop

Each round represents one bounded product iteration.

Example:

* 20k token execution budget
* one small feature per persona
* all work must fit inside one implementation round

Large work MUST be split into smaller rounds.

Ocean strongly prefers:

* small
* reversible
* measurable
* composable
* high-leverage changes

---

# Round Phases

## Phase 1 — Context Assembly

Ocean assembles context:

* doctrine documents
* feedback history
* recent updates
* current roadmap
* telemetry
* active tasks
* peer history
* available tools
* current constraints

Example constraints:

* token budget
* security rules
* allowed APIs
* latency budget
* infrastructure budget

---

## Phase 2 — Research

Each persona independently researches.

Personas may:

* search web
* inspect competitors
* inspect telemetry
* inspect logs
* inspect recent commits
* inspect product analytics
* inspect peer work
* inspect proprietary sources

Each persona chooses its own research strategy.

Example:

* Edna researches onboarding friction
* Mario researches infrastructure costs
* Tony researches bug patterns
* Q researches competing architectures
* Moroni researches strategic positioning

Research budget is bounded.

---

## Phase 3 — Proposal Drafting

Each persona generates 3 candidate ideas.

Each proposal MUST include:

* title
* rationale
* expected user value
* effort estimate
* implementation scope
* acceptance criteria
* risks
* dependencies
* success metric
* why now

Each persona selects its strongest proposal.

Only one proposal advances per persona per round.

---

## Phase 4 — Proposal Board

All selected proposals are published globally.

The board is:

* globally readable
* locally writable

Meaning:

* every persona may read every proposal
* personas may ONLY edit their own proposal

No direct peer editing.

This prevents:

* vandalism
* proposal hijacking
* collusion
* chaotic rewrites

---

## Phase 5 — Peer Analysis

Each persona analyzes peer proposals.

They inspect:

* overlaps
* conflicts
* missing evidence
* hidden risks
* sequencing opportunities
* duplicated work
* strategic gaps
* stronger framing
* leverage opportunities

Personas do NOT vote.

Personas learn.

---

## Phase 6 — Self Revision

After reading peers, each persona may revise ONLY its own proposal.

Allowed revisions:

* tighten scope
* split oversized work
* reduce risk
* improve rationale
* improve acceptance criteria
* improve sequencing
* add evidence
* withdraw proposal
* replace with stronger idea

This creates emergent adaptation without centralized rewriting.

Rule:

> Read globally. Write locally. Synthesize centrally.

---

## Phase 7 — Ocean Synthesis

Ocean reads all final proposals.

Ocean identifies:

* dependency chains
* duplicate ideas
* hidden leverage
* sequencing problems
* oversized work
* conflicting changes
* strategic misalignment
* infrastructure unlocks

Ocean ranks proposals by:

```text
Expected User Value
÷
Implementation Cost
```

Adjusted by:

* strategic fit
* reversibility
* maintenance burden
* future leverage
* operational risk
* doctrine alignment

---

## Phase 8 — Build Queue

Ocean creates ordered build queue.

Ocean eventually builds ALL bounded valid work.

The competition is NOT:
“what gets built.”

The competition is:
“what should happen next.”

Priority is the scarce resource.

---

## Phase 9 — Execution

Ocean dispatches work to coding agents.

Possible backends:

* Codex
* Cursor
* Claude
* OpenAI API
* MCP clients

Ocean itself does not directly code.

Ocean orchestrates:

* sequencing
* delegation
* verification
* synthesis

---

## Phase 10 — Verification

Ocean verifies:

* tests
* acceptance criteria
* telemetry impact
* regressions
* UX quality
* operational impact
* downstream effects

Ocean asks:

> “Did this actually improve the product for the intended user?”

Not merely:

> “Did the code compile?”

---

## Phase 11 — Feedback Capture

Ocean records:

* user reactions
* telemetry
* bugs
* support signals
* friction
* adoption
* maintenance burden
* reversions
* implementation cost

Feedback becomes durable memory.

---

## Phase 12 — Persona Memory Update

Each persona maintains evolving memory:

* successful proposal patterns
* failed proposal patterns
* peer tendencies
* strategic lessons
* user preferences
* implementation outcomes
* hidden leverage discoveries

Personas adapt over time.

The system is evolutionary.

---

# Reputation System

No currency economy.

No compounding voting power.

No permanent capital dominance.

Reputation is informational only.

Ocean tracks:

* proposal success rate
* value density
* sequencing quality
* risk prediction accuracy
* implementation leverage
* user outcome quality
* strategic coherence

Purpose:

* improve future reasoning
* improve trust calibration
* improve synthesis quality

NOT:

* control governance

All personas retain equal proposal bandwidth.

---

# Stability Properties

This system remains stable because:

* proposal bandwidth is equal
* voting power does not compound
* all personas continue participating
* work units are bounded
* proposals evolve through peer visibility
* doctrine anchors identity
* evidence updates priorities
* Ocean maintains synthesis authority

The system encourages:

* decomposition
* prioritization
* leverage thinking
* strategic adaptation
* user-centered iteration
* operational discipline

The system discourages:

* giant rewrites
* feature spam
* local optimization
* architectural ego
* token waste
* runaway governance capture

---

# Fundamental Principle

Ocean is not trying to maximize features.

Ocean is trying to maximize:

* user value
* learning velocity
* strategic coherence
* value per token
* value per engineering hour

The personas are not players in a game.

They are specialized cognitive pressures inside an evolving autonomous software organization.
