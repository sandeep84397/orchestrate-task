# Adapter: codex (native)

Use when the orchestrator runs in the Codex app and the `mcp__codex_app__*` thread tools
exist. Codex CLI alone (no thread tools) → `cli-fallback.md` with `codex` as the CLI.

Invocation: `$orchestrate-task …` (or pick it from `/skills`). Explicit-only via
`agents/openai.yaml` → `policy: allow_implicit_invocation: false`.
**Follow the live `mcp__codex_app__*` schemas when they differ from this page.** Codex
calls a visible task a *thread*.

| Operation | Implementation |
|---|---|
| detect | `mcp__codex_app__create_thread` exists. |
| run folder | `~/.orchestrate-task/runs/<run-name>/`. Write-test it at Phase 0: if the lead's sandbox asks for approval on every write there, use `<repo>/.orchestrate-run/<run-name>/` instead (excluded like `.orchestrate/`). |
| status path | Children may be sandboxed to their worktree: `<worktree>/.orchestrate/STATUS.md`, evidence `<worktree>/.orchestrate/evidence/`. The child creates them from the template in its brief. The orchestrator excludes the folder once per repo: `echo .orchestrate/ >> "$(git -C <repo> rev-parse --git-common-dir)/info/exclude"`, finds each worktree path with `git -C <repo> worktree list --porcelain`, and reads both by absolute path. |
| title | `set_thread_title`: lead = run name; children = `<RUN> · M<n> · <name>`. |
| group | Sidebar sections only if the user wants them; otherwise the title prefix is the group. Record it. |
| base branch | Worktrees only see committed files and may start detached. Ensure a local branch at the base SHA (`git branch <run>-base-M<n> <sha>`) and pass it as the base if `create_thread` accepts one; the brief's first step is `git switch -c <branch> <sha>` when HEAD is detached. |
| start child | `list_projects` for the project id (worktree mode for a git repo), then `create_thread` with prompt = brief and `model`/`thinking` from RUN.md `work`. Asynchronous: write the register row first. A `clientThreadId` is pending; resolve it to a stable `threadId` + `hostId` via `list_threads`, matching the run id + milestone key inside the prompt, never a similar title. Unresolved → mark it uncertain and don't create a duplicate. Emit `::created-thread{threadId="..."}` in your reply for each child. |
| message | `send_message_to_thread` (on an idle thread a follow-up starts a turn). |
| sweep | `list_threads` with a wide `limit` (no cursor); look up each registered id directly, since missing from a bounded listing ≠ failed. Use `wait_threads` (stable ids, host ids, per-target `afterCursor`, longest allowed timeout) only at the end of a tick, as the wait until the next event. |
| events | `read_thread` with small bounds. |
| restart child | First try `send_message_to_thread` on the old thread with the restart prompt. Only if it is dead and confirmed idle (there may be no stop tool): a new thread in local mode on the existing worktree (a new worktree can't check out a branch already checked out). |
| change child model | `send_message_to_thread` with `model`/`thinking`. |
| subagent | `spawn_agent` (`agent_type`, `model`, `reasoning_effort`, `task_name`), then `wait_agent` for a mailbox update; consume the delivered final answer or message and save the report. Use `list_agents` to inspect status, `send_message` for a running agent, or `followup_task` to continue an idle agent when needed. `interrupt_agent` stops an active turn only when needed, never for normal completion. Codex's own prompt says not to set a model unless asked; this skill asks, so pass RUN.md's choice. Stay within `[agents] max_threads` (newer builds: `max_concurrent_threads_per_session`). |
| heartbeat | `automation_update`: one heartbeat per run, pointing at the lead thread and the register path; interval from RUN.md (the minimum allowed if 5m isn't). Reconcile an existing automation id first; remove it at close-out. Never promise a wake-up before creation succeeds. |
| complete | Record child completion in `REGISTER.md` and `BOARD.md`; leave the thread available. Archive separately, only after the user's yes, with `set_thread_archived` (stable id + host id). Archiving does not stop a thread or merge its work. |
| ask user | Plain text in the lead thread. |

## Model discovery
Read `~/.codex/models_cache.json` (Codex refreshes it): slug, description, default and
supported reasoning efforts; skip hidden entries. Tier by the descriptions (frontier →
plan/review, latest workhorse → work, fast/cheap → light mechanical work).
`codex exec --help` confirms flags. The cache can list models your sign-in can't use:
probe each one (`references/models.md`) before proposing it.

## Persona agents (`principal`)
`~/.codex/agents/*.toml` and `<repo>/.codex/agents/*.toml`. A `model` in the agent file
overrides the spawn value.

## As a read-only CLI for another platform's plan/review
See `references/models.md`.
