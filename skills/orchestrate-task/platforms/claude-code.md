# Adapter: claude-code (native)

Use when the orchestrator runs in the Claude desktop app (Code tab), where the
`mcp__ccd_session__*`, `mcp__ccd_session_mgmt__*` and `mcp__ccd_sidebar__*` tools exist.
Plain Claude Code CLI without them → `cli-fallback.md` with `claude` as the CLI.

Invocation: `/orchestrate-task …`. Explicit-only via `disable-model-invocation: true`.
Some tools are deferred: load them with ToolSearch (`select:<name>`) before first use.

| Operation | Implementation |
|---|---|
| detect | `mcp__ccd_session__start_session` exists (directly or deferred). |
| run folder | The app's shared notes folder for this session (`~/Library/Application Support/Claude/side-session-notes/<this-session-local-id>/`) when named; else `~/.orchestrate-task/runs/<run-name>/`. Children can write here (check on the first `STATUS?`; if a child gets permission prompts, switch to the `<worktree>/.orchestrate/` status path used by the other adapters). |
| status path | `<run>/milestones/M<n>/STATUS.md`; evidence `<run>/milestones/M<n>/evidence/`. |
| title | `mcp__ccd_session_mgmt__set_session_title` on self. |
| group | `mcp__ccd_sidebar__create_group` (run name); `mcp__ccd_sidebar__move_sessions` for this chat and every child. Record the group id. |
| base branch | `start_session` cuts from a branch: `git branch <run>-base-M<n> <sha>` (local only, never pushed). |
| start child | `mcp__ccd_session__start_session`: `initiation: "user_asked"`, `context: "fresh"`, `use_worktree: true`, `cwd` = repo, `source_branch` = `<run>-base-M<n>`, `branch_name` = plan slug, `title`, `name`, `prompt` = brief, `background` ≥80 chars. `model`/`effort` from RUN.md `work` only when it names one (at or below this session's). Leave `permission_mode` unset: children match this chat, and a child in another mode may hold messages. Write a bold title line + one sentence before each call. Record the `local_…` id, the actual branch (the app adds a prefix/suffix) and `permissionMode` (`get_session`). |
| message | `SendMessage`, `to` = `local_…` id, `notify_when_idle: true` for `NEXT`/`GUIDE`/`REVIEW`/`GATE`/`DONE`. Arrives at the child's next tool round. |
| sweep | `mcp__ccd_session_mgmt__list_sessions {"group": "<group id>", "limit": 50}` → `isRunning`, `lastActivityAt` per registered id. Not `linked`: it is empty after an orchestrator restart. |
| events | `mcp__ccd_session_mgmt__list_events` (last 5–20). |
| restart child | `start_session` with `use_worktree: false`, `cwd` = the existing worktree, restart prompt from `references/pull-loop.md`. Move it into the group. |
| change child model | `mcp__ccd_session_mgmt__set_session_model` / `set_session_effort`. |
| subagent | Agent tool: `subagent_type` (`Plan` for planning, `general-purpose` for reviews, the persona type for `principal`), `model` + `effort` from RUN.md, `run_in_background: true` for reviews. |
| heartbeat | `loop` skill: `<interval> <tick prompt>` (SKILL.md, Setup). Stop by ending the loop. |
| complete | `mcp__ccd_sidebar__mark_completed`; archive (`mcp__ccd_session_mgmt__archive_session`) only on the user's yes. |
| ask user | Plain text, as a card (`references/chat-ux.md`); the text card is the source of truth. Optional mirror on turns that show a card and already call `mcp__ccd_turn__wrap_up`: `ask` = the card's headline (≤100 chars), `actions` = the recommended reply first (e.g. "ok, merge M2") and one alternative ("Hold"), `recap` = 2–3 plain sentences (where the run stands). Never on quiet event turns. |

## Async arrivals (keep the chat quiet)
The app relays each child's turn end (`<side-sessions-event>`, first 400 chars) and any
cross-session message into this chat, and every subagent hand-back starts a turn. Each
is a manager-loop trigger: process it, then reply per lane (`references/chat-ux.md`) —
no visible reply, or one card. Never answer one with a multi-milestone report.
- Turns with nothing for the user: if the heartbeat runs self-paced on `ScheduleWakeup`,
  pass `noop: true` so quiet ticks collapse. Relayed reports, hand-backs and
  fixed-interval ticks can't be marked no-change: end them with the one fixed line from
  `references/chat-ux.md` (`·`, or the short blocker line).
- Board beside the chat: the run folder is the session's shared notes folder, so open
  `BOARD.md` once with `mcp__ccd_view__show_pane` at setup. Skip if unavailable.
- Blocker alerts unchanged: `PushNotification`, pin + mark unread (pull-loop.md). Any of
  these tools missing (load deferred ones with ToolSearch first) → skip it and say so
  once in RUN.md.

## Model discovery
1. The Agent tool's `model` parameter lists the model aliases subagents can use; its
   `effort` parameter lists effort levels.
2. This session's environment info names the current model family and full model IDs.
3. Tier them (most capable → plan/review; this session's model or the main coding model
   → work). Unclear → propose and let the user pick.

## Persona agents (`principal`)
`~/.claude/agents/*.md` and `<repo>/.claude/agents/*.md`: the file name is the
`subagent_type`.

## As a read-only CLI for another platform's plan/review
See `references/models.md`.
