# Codex task protocol (lite)

Follow the live `mcp__codex_app__*` schemas if they differ from this page. These tools call a visible task a "thread".

## Tools

| Need | Tool / rule |
|---|---|
| Project | `list_projects` → project ID and `isGitRepository`. Worktree mode when it is a git repo, local otherwise; honor an explicit user preference. Cloud only on request. |
| Create a worker | `create_thread`, only when the user asked for orchestration. |
| Wait | `wait_threads` with stable IDs, host IDs and per-target `afterCursor`, using the longest timeout the schema allows. Do lead work (review, merges, register) between waits instead of re-waiting quickly. |
| Answer, rework, contract bump | `send_message_to_thread` (can also set `model`/`thinking`). Use a follow-up that starts a turn for an idle task. |
| Inspect | `read_thread`, small bounds, only after an actionable report |
| Find work | `list_threads` (has `limit`, no cursor — widen the limit), `list_archived_threads` |
| Archive | `set_thread_archived` with the stable thread ID and host ID |
| Titles | `set_thread_title` with a `T01 · <item>` prefix. Sidebar tools only if the user wants grouping. |
| Continue later | `automation_update` heartbeat, only if the user asks |

## Identity

- `create_thread` is asynchronous. Write the item to the register first, then record the response.
- A `clientThreadId` is pending. Never pass it to tools that need `threadId`; resolve it to a stable `threadId` + `hostId` from listings or completion data first.
- If creation is uncertain, match the run ID and item key inside candidate prompts — never a similar title. Unresolved → mark uncertain and tell the user; do not create a duplicate.
- Emit `::created-thread{threadId="..."}` (or `clientThreadId` if still pending) in your final response for each task you created. Use returned titles verbatim.

## Register

Lead is the only writer. Update on state change only.

```markdown
# R1 — <outcome>
Authorized: <...>; NOT: push/deploy
Integration branch: feat/x, base <sha> · Contract: contracts/api.md v1
| Key | Task ID | Model | Status | Owns | Branch @ SHA | Review |
|---|---|---|---|---|---|---|
| B1 | thr_… | Sol/medium | review | backend/auth/** | wt/b1 @ 9d0e7f3 | lead |
Questions: Q-1 (A1) refresh on 401? → yes, contract v2 · closed
Log: 12:05 contract v1 committed; B1, A1 dispatched
```

Statuses: `queued → running → review → accepted → integrated → archived`, plus `rework`, `blocked`, `superseded`, `cancelled`.

## Gates

- `READY_FOR_REVIEW` puts an item in `review`, never straight to `accepted`. The reviewer re-runs the checks in the worker's worktree or a detached checkout of its SHA, never in the lead's checkout.
- Merge only `accepted` items, by SHA, one at a time; run combined checks after each; revert a merge that breaks them.
- Archive automatically only when the work is committed, merged (or `integration: not applicable` recorded), combined checks pass, no question is open, and the task is idle.
- An explicit user archive request is honored, but record unfinished work. Archiving does not stop a task; if its execution status is unknown, keep its write lock and say so.
- Never archive the lead unless asked. Leave blocked and review-pending tasks visible.

## Questions

`Q-<n>` in the register: open → answered → closed. Answer blockers immediately; batch only non-urgent ones. The lead closes a question when the worker's next report shows the answer was used. A revised question gets a new ID.

## Resume

Read the register, then look up each recorded task directly by ID (a task missing from a bounded listing has not necessarily failed). Verify existing outputs before redoing work. Only then dispatch anything new.

## Stalls

Stalled means idle across two waits with no pending checkpoint. Send one continuation. If it stays idle, re-brief a fresh task — but only once the first is confirmed idle, since there may be no stop tool.

## Heartbeat (only if requested)

Reconcile any recorded automation ID before creating one. One heartbeat per run, pointing at the lead thread and register path; notify only on completion, failure, or needed user action; remove it when the run ends. Never promise a wake-up before creation succeeds.
