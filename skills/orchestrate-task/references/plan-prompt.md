# Planning prompt (Phase 1)

Send to RUN.md's `plan` role, read-only (op `subagent`, or another platform's CLI).
Fill every `<…>`. Prepend the project config's communication-style line, if any.

---

You are designing a milestone plan for parallel execution by independent agent
sessions. Read-only: do not edit, run builds, deploy, or open PRs.

## Goal
<goal / ticket list / linked plan>

## Repos and bases (fetched just now)
<repo path · remote branch · SHA> (one per line)
Known dirty/paused worktrees or branches touching this area: <list or none>

## Project constraints
<paste the relevant project config: test commands, devices + lease rules, deploy
rules, frozen-by-default hotspots, review model, personas>

## What to produce
Follow the PLAN template exactly (sections 0–7 below). Mark every factual claim
VERIFIED (you read it at a cited `file:line` / SHA / PR) or ASSUMED.

Rules the plan must satisfy:
1. **Milestones run in parallel and never block each other.**
   - Every file path is owned by exactly one milestone (or nobody).
   - Shared hotspots (build files, navigation graph, shared strings/resources, DB
     schema/migrations, DI root, API spec, deploy/infra config, CI) are FROZEN; the
     orchestrator is the single writer. List them.
   - Merges and deploys are executed by the orchestrator after user approval.
   - Every interaction between milestones is a numbered frozen contract (C1…):
     endpoint shape, symbol signatures (additive-only), schema versions. State it
     precisely enough to write a fake against.
   - Anything that would conflict goes into ONE milestone, in order. Say what you
     forced together and why.
2. **Goals within a milestone run strictly in order.** 3–6 goals per milestone. Each
   goal ≤1 day, produces one evidence bundle (files `g<k>-*`), and has at most one user
   approval gate, at its end (mark `[gate: …]`).
3. **Strict TDD per code goal:** principal review of layering + test list
   first → RED run saved → minimal fix → GREEN run saved → mutation check (revert the
   fix; the new tests must fail). One goal per test layer or gate is a good default.
4. **Independent testability:** each milestone passes its own suite on its own branch
   from its own base, with fakes/fixtures for consumed contracts. Never needs another
   milestone's code or an undeployed backend. Give the exact command, fixtures,
   device needs and known-red exclusions per milestone.
5. **Shared resources:** list leases (devices, heavy suites, deploy slots), their
   grant order, and safety rules. Children never deploy or merge themselves.
6. List open questions for the user, ordered by how much work each answer unblocks,
   each with a recommended answer and the milestones it unblocks.
7. Keep it tight: about 1,500 words. Tables over prose.

## PLAN template
0. Changed facts since last known state (VERIFIED/ASSUMED)
1. Milestones table: ID · name · repo · base SHA · branch · estimate · owns
   (exclusive) · contracts produced/consumed. Then the FROZEN list. Then contracts
   C1…Cn. Then goals per milestone. Then the testability table.
2. Independence: pairwise why each pair cannot block; what was forced together.
3. Shared resources and lease order; deploy plan.
4. Merge order and the final integration check (after merges, never first proof).
5. Open questions for the user (ordered, with recommendation + unblocks).
6. One-paragraph brief per milestone (scope, done, never-touch).
7. Risks and unverified assumptions. Critical files list.
