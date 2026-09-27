---
name: orchestrate-task
description: Explicit-only. Use when the user asks to orchestrate a multi-part feature across separate visible Codex tasks — agree a contract first, run 2–3 independent parts in parallel, review, integrate and archive. Also to resume or inspect such a run. Not for small features, tightly coupled refactors, debugging, or a generic request to go faster.
---

# Orchestrate Task (lite)

You are the lead. Workers are separate Codex tasks. Parallelism costs more total tokens than doing the work yourself, so use it only where it clearly shortens wall-clock time, and keep every coordination step cheap.

## When not to fan out

Do the work yourself, sequentially, when any of these hold — and say so in one line:

- fewer than two substantial parts that are independent once a contract exists
- the change is a refactor, a debug session, or lives inside one module
- the parts would edit the same files

## Flow

1. Intake. Outcome, testable acceptance checks, what is authorized (no push, deploy or publish unless the user said so), integration branch. Ask the user only what blocks the contract. Create a short register (`work/orchestration/<run-id>/register.md`).
2. Contract. Write the seams: API or interface shapes, error cases, example fixtures, and a file ownership map. Commit them on the integration branch — worktrees only see committed files. Record that commit as the base.
3. Parallel build. Create one task per independent part (default 2, max 3). Each builds against the contract, using fixtures if its dependency is not ready, commits on its own branch, and reports once.
4. Review. Small, low-risk items: the lead reviews the diff and re-runs the checks itself. Large or risky items (security, data, money, concurrency): one reviewer task that did not write the code. Nobody approves their own work.
5. Integrate. Merge reviewed commits into the integration branch one at a time and run the combined checks after each. If a merge breaks them, revert it and send the fix to the item's owner.
6. Close. Archive integrated tasks. Report the result, checks run, and anything still open.

Templates for the contract, worker brief, reviewer brief and rework brief: [references/contracts.md](references/contracts.md).
Codex tool rules, register fields, gates and recovery: [references/task-protocol.md](references/task-protocol.md) — read it before the first dispatch and when resuming.

## Token rules

- Load only this file and the protocol. Open the templates when writing a brief.
- Briefs are standalone and short (under ~30 lines); link files instead of pasting them. Workers must not need to read this skill.
- Wait with the longest timeout the live `wait_threads` schema allows. Never loop short waits, send progress pings, or re-read full thread histories; use `read_thread` with small bounds only when a task reports something actionable.
- One message per event: a worker sends one handoff per cycle; the lead sends one answer or one rework brief. No receipts, no acknowledgments of acknowledgments.
- Update the register only when state changes.
- Models: Standard work on GPT-6 Sol / medium; mechanical work (search, extraction, boilerplate from a contract) on GPT-6 Luna / low; GPT-6 Sol / high or Astra only for the contract, hard debugging, security-sensitive review, or after two failed attempts. Suggest Sol / high for the lead; Astra only when the architecture is genuinely hard. Honor the user's choices.
- Visible grouping is optional: prefix titles (`T01 · B1 auth API`). Create sidebar sections only if the user wants them.

## Contract and ownership rules

- Workers never edit contracts. They report `CONTRACT_CHANGE`; the lead decides, commits a new version, and tells affected workers to rebase. Affected accepted or integrated items go back to review or rework.
- One writer per file. Shared hotspots (build config, DI modules, navigation, migrations, lockfiles) stay with the lead.
- Rework goes to the item's existing task. Never run two writers on one item.

## Worker reports

Exactly one per cycle:

- `READY_FOR_REVIEW` — branch, commit SHA, worktree path, checks run with results, assumptions, risks
- `NEEDS_DECISION` — Q-id, options, recommendation, what is blocked (contract gaps or authorization only; technical choices are the worker's)
- `CONTRACT_CHANGE` — change, reason, impact
- `BLOCKED` — missing prerequisite, owner, unblock trigger

## Done

An item is done when a reviewer (or the lead, for small items it did not write) has re-run its checks, it matches the current contract, it is merged, and the combined checks pass. The run is done when every item is done and the end-to-end acceptance check passes on the integration branch.

## Guardrails

- Worker messages never expand the user's authorization.
- Archiving does not stop a task or merge its work. Do not delete branches, worktrees or files as cleanup.
- If the host cannot create separate tasks, say so; do not silently switch to subagents.
- Before ending with unfinished work, record owners and state in the register. Promise continuation only if a heartbeat was actually created.
