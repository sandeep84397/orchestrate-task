# Models: runtime discovery, roles, commands

Nothing in this skill names a model as a default. Models change too often, so every run
discovers what is available at setup and records its choices in `<run>/RUN.md`.

## Roles

| Role | Does | Suggest from |
|---|---|---|
| `plan` | Designs the milestone plan (Phase 1). Read-only. | The most capable model available, highest effort. |
| `review` | Holistic review at every goal completion. Read-only. | A top-tier model, high effort. Different from `work` when possible: an independent second opinion. |
| `work` | The milestone children who write code and tests. | The platform's main coding model, medium-to-high effort. |
| `principal` | Approves layering and the test list before code (persona agent if the project has one). | A top-tier model, or the persona agent's own model. |

## Discovery (at setup, and on `models refresh`)
1. Follow the active adapter's "Model discovery" section.
2. For each other platform CLI that is installed and signed in, run its adapter's
   discovery too: those models can serve `plan` and `review`.
3. **Probe** every candidate with a trivial read-only call (e.g. "reply OK") on the
   platform that would run it. Model lists can include models the user's account or
   auth mode can't use (a Codex CLI on a ChatGPT sign-in rejected two of the cached
   models with `model_not_found`); drop any that fail and note why in RUN.md.
4. Tier each working model from its own description: frontier / strongest, main
   workhorse, fast / cheap. Unclear → ask the user rather than guess.
5. Propose a role table and ask the user to confirm it (one question).

## Cross-platform roles
`plan` and `review` may run on another platform, because they are read-only: the
orchestrator runs that platform's CLI in read-only mode with the filled prompt and saves
stdout as the report. `work` and `principal` always stay on the orchestrator's own
platform, because starting, messaging and supervising children depends on it.

Write the filled prompt to `<run>/msgs/<role>-<id>.md`; the CLI is told to read it.
Run in the background from the worktree under review (or the repo, for `plan`), and
save the output as the report.

| Platform | Read-only run (confirm flags with `--help`) |
|---|---|
| claude | `claude -p "Read and follow <prompt file>" --model <id> --allowedTools "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Bash(git show:*)" --add-dir <run>` (headless plan mode can deny `git diff`) |
| codex | `codex exec -s read-only -m <model> -c model_reasoning_effort="<effort>" -C <worktree> -o <report file> "Read and follow <prompt file>"` |
| gemini | `gemini -p "Read and follow <prompt file>" -m <model> --approval-mode plan --include-directories <run>` |
| other | headless flag + read-only/plan mode, from `--help` |
 If that CLI fails (not installed, not signed in, quota),
fall back to the orchestrator's own platform, record it in RUN.md, and tell the user in
one line.

## RUN.md (orchestrator-owned, in the run folder)

```markdown
# Run config — <run name>
platform: <adapter> · invoked as <command> · detected <time>
discovered: <time> · sources: <models cache file / Agent tool / CLI --help …>
other CLIs: codex <ver> ✓ signed in · gemini ✗ not installed
available (probed): <platform:model (tier) list> · rejected: <model — reason>

| role | platform | model | effort | why |
|---|---|---|---|---|
| plan | codex | <id> | max | strongest available |
| review | claude-code | <id> | high | independent of work model |
| work | claude-code | <id or inherit> | — | main coding model |
| principal | claude-code | agent `<persona>` | — | project persona |

heartbeat: <interval> via <mechanism> · id: <loop/automation/scheduler id, if any>
child autonomy: <what children may run without asking — cli-fallback only>
confirmed CLI flags: <cli-fallback only>
changes:
- <time> models set review=… (user)
```

## Commands (typed as the skill's argument, or as a plain message mid-run)

| Command | Effect |
|---|---|
| `models` | Show the role table from RUN.md, plus what else was discovered. |
| `models set <role>=[<platform>:]<model>[@<effort>]` | Change one role. Validate the model against the latest discovery (run `models refresh` if it isn't known). Record it under `changes:`. `plan`/`review` apply to the next run of that role; `work` applies to children started or restarted afterwards, and to running children where the adapter has "change child model"; `principal` applies to the next approval. |
| `models refresh` | Rediscover every platform, show what changed, keep the current choices unless one has vanished (then propose a replacement as one question). |
| `platform` | Run `platforms/choose-platform.md`. |

Examples: `models set review=codex:<model>@high` · `models set work=<model>` ·
`models set plan=gemini:<model>`.
