---
name: orchestrate-task
description: Use when the user wants a Codex task to orchestrate separate visible child tasks, choose their models, supervise parallel work, integrate results, and archive verified children. Also use to resume or inspect an existing orchestration. Generic requests to work faster or use subagents alone do not match.
---

# Orchestrate Task

Own the user's complete outcome through separate Codex tasks. "Child" is a relationship recorded by this workflow; do not assume the app implements a native parent-child hierarchy. Do not substitute collaboration subagents for requested visible tasks.

## Start or resume

1. Identify whether you are the parent or a dispatched child. A child follows its assignment and reports back; it does not start another orchestration.
2. Confirm the user's request authorizes separate tasks. Explicit invocation with this skill's task-creation prompt does; automatic skill selection alone does not. Honor current tool instructions and higher-priority limits. If this host disallows the requested separate-task workflow, explain the specific limitation rather than silently switching execution modes.
3. Inspect available task/model controls. Read [task-protocol.md](references/task-protocol.md) before dispatch, recovery, or cleanup. Missing capabilities are limitations, not reasons to invent tools.
4. Establish outcome, acceptance checks, authorized actions, dependencies, and an integration destination. Resolve routine choices yourself. Ask the human only for material missing intent, access, permission, or an unresolved external blocker; continue unaffected work.
5. Reconcile an existing task register with live tasks before creating anything. Otherwise create a register in the task's writable working area. Preserve it across compaction and restart.

## Plan and dispatch

Represent pending work in the register first. Open tasks only when their inputs are ready. Parallelize independent work; keep dependent stages sequential. Small indivisible work can stay with the parent. Use existing related tasks for corrections and follow-ups.

Assign each child an outcome, acceptance checks, owned files or artifact, dependencies, workspace, and reporting protocol. One writer per shared file at a time. Use separate worktrees when isolation helps; record how changes reach the integration destination. Respect user edits. Never assume separate tasks or worktrees automatically share changes.

Choose models from the live supported list. Suggested starting points:

| Work | Model / effort, if available |
|---|---|
| Bounded extraction, search, log summaries | Luna / low or medium |
| Normal implementation, tests, review | Terra / medium |
| Ambiguous architecture, difficult debugging, sensitive decisions | Sol / high or xhigh |
| Hardest reasoning, parent decisions, unusually difficult child work | Astra / supported appropriate effort |

Optimize total completion cost, including retries and integration. Strong children are allowed. Increase effort or change model when evidence warrants it; do not repeatedly send an unchanged failing assignment. Honor user budgets and model choices. Start with a modest active queue, commonly 2–3 children, then adapt to dependencies and observed capacity. Unlimited task creation or concurrency is not guaranteed.

The skill cannot switch its own parent model. Recommend starting the parent with Astra / Extra High when available; disclose the actual model/effort only when verified. No global configuration changes are implied.

## Supervise and finish

Stay active while required child work remains. Use bounded status waits, respond to child questions, and return corrections promptly. Let children make local implementation choices; the parent owns shared contracts, scope, cross-task conflicts, and integration. Keep user updates concise and evidence-based.

Use lifecycle: `queued → creating → running → review → verified → integrated → archived`. Branch to `needs_decision`, `blocked`, or `rework` as needed. A child's DONE report enters review. Passing isolated tests does not prove integration.

Inspect outputs and run proportionate combined checks against the user's acceptance criteria. Resolve failures before completion. Save handoff evidence and verify integration, then archive the completed child using the archive tool. Preserve unresolved tasks. Do not archive the parent unless requested. Honor explicit manual archive/unarchive requests, recording unfinished work accurately.

Finish only with the integrated deliverable and verification evidence, or a precise remaining blocker. Report archived children and any open children with reasons. Before ending with unfinished work, record ownership and a real continuation mechanism; never imply monitoring will continue without an active run or authorized scheduler.
