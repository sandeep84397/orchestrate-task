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
4. Establish outcome, acceptance checks, authorized actions, dependencies, and an integration destination. The applicable domain workflow and execution constraints determine whether human input is required. Orchestration supplies available context, routes remaining dependencies, and keeps unaffected work progressing; it adds no domain approval rules.
5. Reconcile an existing task register with live tasks before creating anything. Otherwise create a register in the task's writable working area. Preserve it across compaction and restart.

## Make ownership visible

Give the parent a stable short manager key, such as `T01`, and record its verified task/host ID. Use one sidebar group per parent, parent first, with matching title prefixes: `Testing · T01`, `T01 · Manager`, `T01 · Auth · QA`. A long-lived manager retains its key across runs. Follow [visible ownership](references/task-protocol.md#visible-ownership) when dispatching or recovering. Group/title labels aid navigation; the recorded task IDs establish the relationship. Preserve explicit user naming/placement choices and never group unrelated tasks by title similarity.

## Plan and dispatch

Represent pending work in the register first. Open tasks only when their inputs are ready. Parallelize independent work; keep dependent stages sequential. Small indivisible work can stay with the parent within the user's role constraints. Assign each child one bounded investigation and deliverable cycle through a review-ready result, including a fix and build/test for code work where applicable. The parent owns context, shared contracts, cross-task decisions, integration and acceptance; avoid intermediate implementation approvals when the child has sufficient inputs and authorization. Return corrections or rework of the same item to its existing owner. For an independent new item, compare the context cost of reusing a long task with a fresh concise child; preserve register IDs and ownership, and never start a duplicate active writer.

Assign each child a [focused context brief](references/task-protocol.md#child-assignment-contract): problem, relevant evidence, known facts versus hypotheses, constraints, acceptance checks including applicable failure/recovery cases, ownership and reporting paths. Provide available verified answers promptly; the child evaluates and applies them. One writer per shared file at a time. Use separate worktrees when isolation helps; record how changes reach the integration destination. Respect user edits. Never assume separate tasks or worktrees automatically share changes.

Choose models from the live supported list. Suggested starting points:

| Work | Model / effort, if available |
|---|---|
| Bounded extraction, search, log summaries | GPT-6 Luna / low or medium |
| Normal implementation, tests, review | GPT-6 Sol / medium |
| Ambiguous architecture, difficult debugging, sensitive decisions | GPT-6 Sol / high or xhigh |
| Hardest reasoning, parent decisions, unusually difficult child work | GPT-6 Astra / supported appropriate effort |

Optimize total completion cost, including retries and integration. Strong children are allowed. Increase effort or change model when evidence warrants it; do not repeatedly send an unchanged failing assignment. Honor user budgets and model choices. If an explicitly selected model is unavailable, report the failed selection and ask the parent before using a different model. When the user requests token measurement, record each task's start/end cached, uncached and output tokens where available; shared account usage percentages are not per-task cost. Start with a modest active queue, commonly 2–3 children, then adapt to dependencies and observed capacity. Unlimited task creation or concurrency is not guaranteed.

The skill cannot switch its own parent model. Recommend starting the parent with Astra / Extra High when available; disclose the actual model/effort only when verified. No global configuration changes are implied.

## Supervise and finish

Stay active while actionable child work remains. After dispatch, wait for the child's review-ready result without progress pings; status waits are read-only and do not interrupt the child. Contact it sooner only for an actionable child question/blocker, shared-resource contention, a changed shared contract, urgent risk or user direction. Children proceed independently within sufficient context and authorized scope. Request one consolidated review-ready handoff per bounded cycle, with changed evidence and references to existing artifacts. Review that result against the original acceptance checks. If it misses a check, send one clear rework brief with expected versus actual behavior, evidence, scope and required correction, then wait for revised completion. The parent owns shared contracts, scope, cross-task conflicts, integration and evidence-based acceptance; it does not take over a child's implementation to answer a question. Keep user updates concise and evidence-based.

Questions and decisions flow both ways: parent → child and child → parent. Both sides maintain durable pending-message records and acknowledge answers. Follow the [bidirectional request queue](references/task-protocol.md#bidirectional-request-queue), and include its paths and contract in child assignments. Delivery is not resolution. Reconcile open exchanges on resume and before pause, handoff, or archive. These operating rules belong to this skill; Agent Brain may retain outcomes but is not the live queue.

Keep coordination proportional: batch transport for nonurgent independent questions to the same recipient while retaining one canonical ID/state per question. A receipt may be piggybacked on a substantive reply or an already-needed progress message; send an ACK-only turn only when a blocker needs ownership before the next useful message. Retain one canonical parent record per exchange and compact child references to unresolved IDs/state plus closed-ID answer/evidence lookup, not copied histories. Reuse injected or current Agent Brain context; retrieve only when needed context is missing or stale, and log only when a material decision, changed risk, code-change gate, or outcome requires it.

Use lifecycle: `queued → creating → running → review → verified → integrated → archived`. Branch to `needs_decision`, `blocked`, or `rework` as needed. A child's DONE report enters review. Passing isolated tests does not prove integration. Superseded or authorized-cancelled work has a separate closure path under [cleanup](references/task-protocol.md#integration-and-cleanup); preserve that disposition after archive.

Inspect outputs and run proportionate combined checks against the user's acceptance criteria, including relevant negative, recovery and regression cases. Track an independently discovered defect or coverage gap as a separate owned item within authorized scope. The original item may close after its own acceptance and integration gates pass; keep the new item and overall outcome open until resolved. Save evidence and verify integration, then archive eligible children using the protocol's closure gates. Preserve unresolved tasks. Do not archive the parent unless requested. Honor explicit manual archive/unarchive requests, recording unfinished work accurately.

Finish only with the integrated deliverable and verification evidence, or a precise remaining blocker. Report archived children and any open children with reasons. Before ending with unfinished work, record ownership and a real continuation mechanism; never imply monitoring will continue without an active run or authorized scheduler.
