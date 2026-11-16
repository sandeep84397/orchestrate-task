# Orchestrate Task

An agent skill for running large work as **parallel milestone sessions** managed by one
orchestrator chat. Works on **Claude Code**, **Codex**, and **Gemini CLI / Antigravity /
any agent CLI**.

The orchestrator plans the work into milestones, starts one child session per milestone
(own worktree and branch), and then acts as their manager: it hands out one goal at a
time, reviews every finished goal, unblocks or guides stuck children, keeps them from
sitting idle, and asks you one question at a time.

Parallel work costs more tokens than sequential work. Use this when it clearly saves
wall-clock time on work that splits into independent milestones. For small features,
single-module refactors or debugging, ask the agent directly.

## How it works

1. **Platform and models.** Detects where it runs, discovers the models available
   *right now* (nothing is hardcoded), and proposes a model per role: `plan`, `review`,
   `work`, `principal`. You confirm or change it.
2. **Plan.** The `plan` model splits the work into milestones of 3–6 ordered goals
   (each ≤1 day, one evidence bundle, at most one approval gate). Every file has one
   owner; shared hotspots and cross-milestone contracts are frozen. The orchestrator
   checks the planner's claims against the code, then asks you to approve.
3. **Children.** One child session per milestone, in its own worktree, briefed with its
   owned files, frozen files, contracts, test commands and done-definition.
4. **Strict TDD per goal.** Failing tests first (saved), minimal fix (saved), mutation
   check (revert the fix, new tests must fail).
5. **Manager loop.** A heartbeat sweeps every child, then handles each one that needs
   something: confirm the goal and send the next one, run the review, answer a blocker
   itself or with a concrete approach, grant a device lease, or queue a question for you.
   Children never message the orchestrator; it pulls their status files.
6. **Review every goal.** The `review` model judges each goal against the whole run:
   tests, layering, contracts, cross-milestone and integration risk.
7. **Merge and integrate.** Merges and deploys happen only after your yes, one at a
   time. The integration check runs after merges.

## A quiet chat

Children report all the time, but you only watch the orchestrator. So the chat shows
**one thing at a time**:

- **Needs you** (a blocker, an approval, a question) → one card with the orchestrator's
  recommendation. Reply "ok" or choose another option. The rest of the queue is just a
  count. Only a blocker jumps the queue.
- **Good to know** (goal done, review passed, test passed) → collected into a short
  digest every 30 minutes, or when you type `digest`.
- **Bookkeeping** → files only. Child updates that need nothing from you get no reply
  in the chat.

`BOARD.md` in the run folder always shows the full picture; `status` prints it.
`quiet`, `normal` and `verbose` change how much reaches the chat.

## Commands

| You type | Does |
|---|---|
| `/orchestrate-task <goal or tickets>` (Codex: `$orchestrate-task …`) | Start a run |
| `… resume <run folder>` | Continue a run from its files, e.g. in a new chat |
| `… models` | Show the model for each role |
| `… models set review=codex:<model>@high` | Change a role (`plan` and `review` may use another platform's CLI, read-only) |
| `… models refresh` | Rediscover models |
| `… platform` | Compare the platforms installed on this machine and get a recommendation |
| `status` / `board` / `blockers` · `next` · `digest` · `details M3` (mid-run) | Board · current or next card · news · one milestone's recent events |
| `quiet` · `normal` · `verbose` (mid-run) | How much reaches the chat |

## Platforms

| | Claude Code (desktop app) | Codex (app) | Gemini CLI / Antigravity / any CLI |
|---|---|---|---|
| Children | Visible sessions in a sidebar group | Visible threads | Background headless runs + logs |
| Heartbeat | Built in (`loop`) | Built in (automation) | cron / launchd / shell loop, or manual |
| Explicit-only | Yes | Yes | Gemini: `/skills disable orchestrate-task` + a custom command (see `platforms/cli-fallback.md`) |

Run `/orchestrate-task platform` to see which fits your machine.

## Install

The skill folder is `skills/orchestrate-task/` (keep `platforms/`, `references/`,
`agents/`).

```bash
git clone https://github.com/sandeep84397/orchestrate-task.git
```

Then link or copy the folder where your agent looks for skills:

| Agent | Location |
|---|---|
| Claude Code | `~/.claude/skills/orchestrate-task` |
| Codex | `~/.agents/skills/orchestrate-task` (or `$CODEX_HOME/skills`) |
| Gemini CLI | `~/.agents/skills/orchestrate-task` or `~/.gemini/skills/orchestrate-task` |

One clone with symlinks keeps every agent on the same version:

```bash
ln -s "$PWD/orchestrate-task/skills/orchestrate-task" ~/.claude/skills/orchestrate-task
```

```bash
ln -s "$PWD/orchestrate-task/skills/orchestrate-task" ~/.agents/skills/orchestrate-task
```

Restart the agent if the skill doesn't appear. On Claude Code and Codex the skill is
explicit-only: it never starts sessions unless you invoke it. Gemini CLI has no such
flag; see `platforms/cli-fallback.md` for how to keep it from activating on its own.

## Project config

Per-project facts (repos, test commands, devices and leases, frozen hotspots, gates,
board) live outside the skill at `~/.config/orchestrate-task/projects/<project>.md`.
The first run in a new project creates it from
`references/project-config-template.md` and asks you for anything it can't find.
Models are never stored there.

## Files

- [SKILL.md](skills/orchestrate-task/SKILL.md): commands, rules, phases
- [platforms/](skills/orchestrate-task/platforms): `claude-code`, `codex`, `cli-fallback` adapters and `choose-platform`
- [references/models.md](skills/orchestrate-task/references/models.md): discovery, roles, `models` commands
- [references/pull-loop.md](skills/orchestrate-task/references/pull-loop.md): manager loop
- [references/chat-ux.md](skills/orchestrate-task/references/chat-ux.md): what reaches the chat — lanes, cards, digest, board
- [references/](skills/orchestrate-task/references): plan prompt and template, child brief, status/register formats, goal review prompt
- [tests/regression-scenarios.md](skills/orchestrate-task/tests/regression-scenarios.md): replay checklist

## Validation status

The regression scenarios are replay checklists, not automated tests. The milestone
process ran live on Claude Code (four milestones, Android + backend) before it was made
platform-neutral; the Codex and CLI adapters have not had a recorded live run yet.

## License

[MIT](LICENSE). Independent community skill; not an official product of Anthropic,
OpenAI or Google.
