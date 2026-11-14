# Adapter: cli-fallback (any agent CLI)

Use when the orchestrator has no native session tools: Gemini CLI, Antigravity CLI,
plain Claude Code CLI, Codex CLI, or any agent CLI with a headless mode. Children are
headless CLI runs in their own worktrees, started from the orchestrator's shell.
**Confirm every flag below with `<cli> --help` at setup** and record the confirmed
commands in RUN.md; CLIs change quickly.

## How it works
- A child is one headless run per turn. It works until its turn ends, then the process
  exits. "Idle" = process exited. A message is delivered by resuming that child's CLI
  session with a new prompt, which starts its next turn.
- **Waiting = ending the turn.** Children never sleep-poll; they write STATUS and end
  their turn, and the orchestrator resumes them when there's news.
- Prompts and messages are never passed inline (shell expansion breaks them): write
  them to a file and pass `Read and follow <abs path>`.
- STATUS.md and evidence live in the child's worktree, which every CLI sandbox can write.

| Operation | Implementation |
|---|---|
| detect | No native session tools; a supported CLI is on PATH. |
| run folder | `~/.orchestrate-task/runs/<run-name>/` with `logs/`, `pids/`, `msgs/`. Write-test it at Phase 0; if the orchestrator's own sandbox can't write there, use `<repo>/.orchestrate-run/<run-name>/` (excluded, see below). |
| status path | `<worktree>/.orchestrate/STATUS.md`, evidence `<worktree>/.orchestrate/evidence/`. The orchestrator excludes it once per repo: `echo .orchestrate/ >> "$(git -C <repo> rev-parse --git-common-dir)/info/exclude"` (works in linked worktrees, where `.git` is a file). |
| title / group | None. The register is the group. |
| base branch | `git -C <repo> worktree add <worktree path> -b <branch> <base sha>`, using the project config's worktree location rule. Record the worktree path. |
| start child | Write the brief to `<run>/msgs/M<n>-0001.md`. From the worktree: `nohup sh -c '<start cmd> "Read and follow <msg file>" > <run>/logs/M<n>-<ts>.jsonl 2>&1; echo $? > <run>/pids/M<n>.exit' >/dev/null 2>&1 & echo $! > <run>/pids/M<n>.pid` (or a detached `tmux` session). `nohup` keeps the child alive after the orchestrator's shell call returns. Capture the CLI session id from the first streamed event (or set it up front where the CLI allows, e.g. `claude --session-id <uuid>`). Never resume by "latest". |
| message | Write it to `<run>/msgs/M<n>-<seq>.md`. Process running (no `.exit` file yet) → also append it to `<worktree>/.orchestrate/INBOX.md` (the brief tells children to read INBOX before each step) and record it as `pending` in REGISTER. Process exited → delete the stale `.exit`, then start the **resume command with the same flags as the start command**, from the worktree, with `"Read and follow <msg file>"`, same `nohup` wrapper. |
| sweep | `.exit` file present → turn ended (code inside; `53`-style turn-limit codes → resume with "continue"). Else `kill -0 <pid>` + mtime of the log and STATUS.md. |
| events | `tail -n 40` of the child's latest log (stream format, so it is never empty mid-turn). |
| restart child | A fresh start command in the same worktree with the restart prompt; new session id. |
| change child model | The next resume or start uses the new model flag. |
| subagent | The CLI's own subagents if it has them (agent files with a `model` field), else a read-only headless run (`references/models.md`). Children that can't spawn subagents ask the orchestrator for the principal review (`plan-review` state). |
| heartbeat | Default, **in-session**: after each tick, run one bounded foreground wait, e.g. `for i in $(seq 1 20); do ls <run>/pids/*.exit >/dev/null 2>&1 && break; sleep 30; done`, then tick again; the user can interrupt anytime. **Unattended** (only if the user asks): a separate headless orchestrator session run by cron/launchd every interval, guarded by `mkdir <run>/tick.lock` (skip if it exists, remove when done), with the same flags as the children, never resuming the user's interactive session; it only sweeps, relays and records, and leaves questions in QUESTIONS.md plus a desktop notification. |
| complete | Remove any scheduler entry; keep worktrees and branches. |
| ask user | Plain text. |

## Commands per CLI (verify with `--help`)

| CLI | Start (streaming output) | Resume | Model | Autonomy for children |
|---|---|---|---|---|
| Gemini CLI `gemini` | `gemini -p "<p>" -m <model> -o stream-json --approval-mode yolo` | `gemini -r <session id> -p "<p>"` + same flags | `-m` | `--approval-mode yolo` (or `auto_edit` + allowed tools) |
| Antigravity `agy` | `agy -p "<p>"` + flags from `agy --help` | from `--help` | from `--help` | from `--help` |
| Claude Code `claude` | `claude -p "<p>" --session-id <uuid> --model <id> --output-format stream-json --verbose` | `claude -p --resume <session id> "<p>"` + same flags | `--model` | `--permission-mode acceptEdits --allowedTools "<test cmds>,Bash(git add:*),Bash(git commit:*)"` |
| Codex `codex` | `codex exec -C <wt> -m <model> --json "<p>"` | `codex exec resume <session id> "<p>"` + same flags | `-m`, `-c model_reasoning_effort=…` | `-s workspace-write`, plus write access to the git common dir and tool caches (e.g. `--add-dir`) and network if tests need it |

Autonomy lets a child run commands without asking. Build the allowed set from the
project's test commands, show the user exactly what children may run, and get a yes
before the first start (one question).

Gemini notes: check which CLI your Google account is served by (Gemini CLI or
Antigravity). Skills load from `~/.gemini/skills/` or `~/.agents/skills/` and are
invoked as `/orchestrate-task`. Gemini has no explicit-only flag; to stop automatic
activation run `/skills disable orchestrate-task` and use a custom command
`~/.gemini/commands/orchestrate-task.toml` with
`prompt = "Read <skill folder>/SKILL.md and follow it. Arguments: {{args}}"`.

## Model discovery
1. The CLI's model list: `/model` menu, a list command if `--help` shows one, or the
   provider's models API when a key is already configured. Otherwise ask the user to
   paste it.
2. Probe each candidate (`references/models.md`); pin exact IDs, since aliases such
   as `pro`/`auto` can point to retired models.
