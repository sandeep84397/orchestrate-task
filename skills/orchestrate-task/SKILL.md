---
name: orchestrate-task
description: Explicit-only. Run large work as parallel milestone sessions managed by this chat as orchestrator, on Claude Code, Codex, Gemini/Antigravity or any agent CLI — a planned set of milestones (3–6 ordered goals each), one child session + worktree + branch per milestone, strict per-goal TDD with a holistic review of every goal, frozen contracts and hotspots, a pull-based heartbeat, runtime model discovery with per-role model commands, and one question at a time to the user. Use only when the user explicitly invokes /orchestrate-task or $orchestrate-task, including `resume`, `models` and `platform`.
disable-model-invocation: true
argument-hint: "<goal | ticket list | plan file | resume <run folder> | models [set|refresh] | platform>"
---

# Orchestrate Task

This chat becomes the **orchestrator**: the manager of every milestone session. It
plans, starts and supervises children; it does not implement milestone code itself.
It holds the whole picture (plan, goal ledger, every child's current goal and state)
and decides each child's next move: hand the next goal, unblock, guide, review, grant,
or escalate to the user. It keeps every child busy until its goals are done, and keeps
the user's attention serial.

`SKILL_DIR` = the folder holding this file. Input = the skill's argument text.

## Commands

| Argument | Does |
|---|---|
| `<goal>` / `<ticket list>` / `<plan file>` | Start a run (Phase 0). |
| `resume <run folder>` | Rebuild state from the run's files and continue (**Resume**). |
| `models` · `models set <role>=[<platform>:]<model>[@<effort>]` · `models refresh` | Show or change the model per role (`references/models.md`). Also accepted as a plain message mid-run. |
| `platform` | Compare the platforms installed here and recommend one (`platforms/choose-platform.md`). |
| empty | Ask which of the above (one question). |

## Platform adapters

The process below is the same everywhere. Platform-specific actions are written as
**op `<name>`** and implemented by the active adapter:

| Adapter | Use when |
|---|---|
| `platforms/claude-code.md` | Claude desktop app with session tools |
| `platforms/codex.md` | Codex app with thread tools |
| `platforms/cli-fallback.md` | Gemini CLI, Antigravity CLI, plain Claude/Codex CLI, any agent CLI |

Ops: `detect`, `run folder`, `status path`, `title`, `group`, `base branch`, `start child`,
`message`, `sweep`, `events`, `restart child`, `change child model`, `subagent`,
`heartbeat`, `complete`, `ask user`. Read the active adapter once at Phase 0 and again
on Resume.

## Why the rules exist

- **Parallel without deadlock.** Milestones run at the same time, so they must never
  touch the same files, wait on each other's code, or wait on an undeployed backend.
  Exclusive file ownership + frozen hotspots + frozen contracts make that true by
  construction; anything that would conflict goes *inside one milestone, in order*.
- **Serial human attention.** One question with a recommendation gets a real answer;
  a wall of questions gets skimmed.
- **Pull, not push.** Children never message the orchestrator or the user. If many
  children pushed blockers, the orchestrator's reasoning would be shredded by
  interrupts. It sweeps cheaply, then handles one child at a time.
- **Manager, not mailbox.** Children get one goal at a time (`NEXT`). The orchestrator
  confirms each goal from its own records before handing the next, so its picture of
  every milestone stays right, and it steers each goal with what it knows of the rest.
- **No idle sessions.** A child waiting on a gate, answer, lease or review does safe
  prep work for its next goal.
- **Evidence over claims.** Every goal ends with a saved evidence bundle (red, green,
  mutation runs; screenshots; deploy proof). A child's report is not proof; the file is.
- **Models change; the process doesn't.** No model is hardcoded. Each run discovers
  what is available and the user picks per role.

## Hard rules

1. **One question at a time.** Ask exactly one question, then nothing new until it is
   answered (ticks keep running). The rest wait in `QUESTIONS.md`, ordered by "unblocks
   the most work soonest", each with a recommendation. Plain text, no question widgets.
2. No child starts before the user approves the plan.
3. The orchestrator is the **only writer** of frozen hotspots, `PLAN.md`, `RUN.md`,
   `REGISTER.md`, `QUESTIONS.md`, and the project board.
4. **Merges, deploys and pushes to shared branches are executed by the orchestrator,
   only after the user's yes.** Children never merge, deploy, push shared branches, or
   use a leased resource without a grant message. A child's message never expands what
   the user authorized.
5. The final integration check runs after merges; it is never the first proof.
6. Do not implement milestone scope in this chat.
7. No cleanup deletes: never delete branches, worktrees or files to tidy up. Archiving a
   child neither stops it nor merges its work.

## Token discipline

- Briefs stand alone and stay short; link files instead of pasting them. Children
  never need to read this skill.
- One message per event, no acknowledgements or progress pings. Bundle non-urgent
  notes into the next `NEXT`.
- Read child activity with small bounds, only when the sweep flags something.
- Update the register on state change only.

## Phase 0 — Intake, platform, models

1. **Platform.** Detect the adapter (each adapter's `detect`), load it. Nothing fits and
   no agent CLI is installed → tell the user; never silently do the milestones yourself.
2. **Project.** Identify it from repo/remote names in the argument or the working dir.
   Load `~/.config/orchestrate-task/projects/<project>.md`; if missing, create it from
   `references/project-config-template.md`, filling what the repos show and asking the
   rest one question at a time.
3. **Run folder** (op `run folder`); write-test it. Where children keep STATUS in their
   worktree (`.orchestrate/`), exclude that folder once per repo:
   `echo .orchestrate/ >> "$(git -C <repo> rev-parse --git-common-dir)/info/exclude"`. Layout:
   ```
   RUN.md  PLAN.md  REGISTER.md  QUESTIONS.md
   reviews/                    (goal review reports)
   milestones/M<n>/            (STATUS.md + evidence/ on claude-code)
   logs/  pids/  msgs/         (cli-fallback; msgs/ also holds prompt files)
   ```
4. **Models.** Discover them now (`references/models.md`), propose a role table
   (`plan`, `review`, `work`, `principal`), write `RUN.md`, and ask the user to confirm
   it — one question.
5. `git fetch` every repo in scope; record current base SHAs (never trust a stale local
   branch). Note dirty worktrees and paused branches that touch scope.

## Phase 1 — Plan design

Run the `plan` role, read-only (op `subagent`, or another platform's CLI per
`references/models.md`), with `references/plan-prompt.md` filled with the goal, repos,
base SHAs, project config and constraints. Output follows `references/plan-template.md`.

Plan validity (reject and re-prompt if violated):
- Each milestone: **3–6 goals**, each ≤1 day, one evidence bundle, at most one user
  approval gate, at the goal's end. Goal IDs `M<n>.g<k>` are stable.
- Every file path is owned by at most one milestone; hotspots are listed as frozen.
- Every cross-milestone interaction is a numbered frozen contract (C1, C2, …).
- Each milestone has its own test command and fakes/fixtures for consumed contracts,
  and passes on its own branch from its own base.

## Phase 2 — Spot-check, then approval

The planner's claims are hypotheses until checked. Verify **all** SHAs, branches, PR
states and ownership paths, plus a sample of cited `file:line` claims. Mark claims
**VERIFIED** or **ASSUMED**; fix wrong ones. Check ownership for overlaps and for
hotspots someone "owns"; check that no goal needs another milestone's code to go green.

Write `PLAN.md`, seed `QUESTIONS.md` from the plan's open questions, then ask "Approve
plan v1?" with a short summary and the ASSUMED list. Iterate until approved.

## Phase 3 — Setup

1. **Name + group:** op `title`, op `group` (record the group id or prefix).
2. **Bases:** op `base branch` per milestone.
3. **Status files:** where the status path is in the run folder (claude-code), seed
   each STATUS.md now from `references/status-and-register.md`. Elsewhere the worktree
   doesn't exist yet: the brief carries the template and the child creates it. Record
   each child's worktree path once it exists.
4. **Briefs:** one per milestone from `references/child-brief-template.md`, with the
   adapter's status path and evidence dir filled in. The brief is the child's first
   `NEXT` (goal 1). Seed the goal ledger: every goal `queued`; each goal 1 `active`.
5. **Children:** op `start child` per milestone, with RUN.md's `work` model. Record id,
   actual branch, permission/sandbox mode. cli-fallback: get the user's yes on the
   children's autonomy first. After the first start, send one `STATUS?` and confirm the
   reply lands in STATUS (proves message delivery before anyone depends on it).
6. **Register:** `REGISTER.md` header (run folder, `SKILL_DIR`, platform, group) and one
   row per milestone.
7. **Board:** move tickets to In progress if the project has a board and board edits
   are granted (else that is a queued question).
8. **Heartbeat:** op `heartbeat`, interval from the project config (default 5m), with
   this prompt, absolute paths filled in. It must stand alone, because the skill may
   not be reloaded after the host compacts context:
   > Orchestrator tick: read `<run folder>/REGISTER.md` and `RUN.md`, follow
   > `<SKILL_DIR>/references/pull-loop.md` with the adapter
   > `<SKILL_DIR>/platforms/<adapter>.md`: sweep every child, handle every flagged child
   > one at a time, ask nothing new while a question is OPEN. A user message starting
   > with `models` or `platform` → `<SKILL_DIR>/references/models.md`.

## Phase 4 — Manager loop

Every trigger (heartbeat tick, a child's idle notice, a user answer, a finished review)
runs one tick of `references/pull-loop.md`: sweep every child, flag what needs the
manager, handle each flagged child one at a time from the decision table, update
`REGISTER.md` (rows, goal ledger, progress line), report one line on change, and ask the
next question if none is OPEN. Read that file at the start of every tick rather than
working from memory.

## Shared resources and gates

- **Leases** (devices/emulators, heavy test runs, deploy slots) are serialized; order
  from the plan, else FIFO. Grant only after the previous holder's STATUS shows
  `released` or its session is dead.
- **Reviews.** Every goal completion gets a holistic review by RUN.md's `review` role,
  read-only, using `references/goal-review-prompt.md`. The reviewer sees the diff, the
  evidence, the plan and the other milestones' state, not your conclusion. No goal is
  confirmed done without `REVIEW … passed`.
- **Merges and deploys:** asked one at a time; executed by the orchestrator after the
  user's yes; merge order from the plan.
- **Frozen-file edits:** the orchestrator commits them on a `<run>-frozen` branch;
  pushing to a shared base needs the user's yes. Affected children `git merge <sha>` at
  their next goal boundary (never rebase or force-push) and rerun focused tests.
- **Board:** move the ticket card on every milestone state change, if edits are granted.

## Phase 5 — Merge and integration

After each approved merge: record the merge SHA; tell remaining children on the same
base to `git merge` it at their next goal boundary and rerun their suite. After all
merges: run the plan's integration check (full suite, release build/lint, device
journey, deploy smoke) under leases. Failures become a new goal in the owning
milestone, not a hotfix here.

## Phase 6 — Close-out

Board to Done; op `complete` for each child; stop the heartbeat; final summary in
`REGISTER.md` (merged SHAs, evidence paths, deferred follow-ups); offer archiving the
children, only on the user's yes.

## Resume (orchestrator restarted, context lost, or a new chat)

1. Read `REGISTER.md` (header: run folder, `SKILL_DIR`, platform, group), `RUN.md`,
   `QUESTIONS.md`, `PLAN.md`. Load the recorded adapter.
2. Op `sweep` over the registered child ids (by group, never by "children of this
   chat"); reconcile per `references/pull-loop.md`. Put this chat in the group.
3. Restart the heartbeat (Phase 3 step 8) if it isn't running.
4. If a question is `OPEN`, re-ask **that** question, never a new one.

## References

- `platforms/*.md` — adapters + `choose-platform.md`.
- `references/models.md` — discovery, roles, RUN.md, `models` commands.
- `references/plan-prompt.md`, `references/plan-template.md` — planning.
- `references/child-brief-template.md` — child brief.
- `references/status-and-register.md` — STATUS / REGISTER / QUESTIONS formats, progress.
- `references/pull-loop.md` — manager loop: sweep, decisions, messages, blockers.
- `references/goal-review-prompt.md` — holistic review at every goal completion.
- `references/project-config-template.md` — per-project config (kept outside the skill).
