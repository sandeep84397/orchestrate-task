# Orchestrate Task (lite)

A Codex skill for large multi-part features: agree the contract first, run the independent parts as 2–3 separate visible Codex tasks, review them, integrate on one branch with checks, and archive what's integrated.

Parallel work costs more total tokens than sequential work. This skill is for cases where it clearly saves wall-clock time: a backend endpoint plus an Android screen plus tests, or independent modules. For small features, refactors, debugging, or anything inside one module, don't use it — ask Codex to do the work directly.

## Install

```text
Use $skill-installer to install the skill from:
https://github.com/sandeep84397/orchestrate-task/tree/main/skills/orchestrate-task
```

Or copy `skills/orchestrate-task/` (keep `references/` and `agents/`) into `$CODEX_HOME/skills` or `~/.codex/skills`. Restart Codex if it doesn't appear.

The skill is explicit-only (`allow_implicit_invocation: false`), so it never starts creating tasks unless you invoke it.

## Use

```text
Use $orchestrate-task to add email/password login. Backend is Ktor,
app is Android Compose. Agree the API contract first, run backend and
app as separate tasks, integrate on feat/login, run the end-to-end
check. Don't push.
```

## How it works

1. Intake: outcome, acceptance checks, what's authorized, integration branch.
2. Contract: interfaces, error cases, fixtures and file ownership, committed on the integration branch.
3. Parallel build: 2 tasks by default, max 3, each on its own branch, one report at the end.
4. Review: the lead reviews small items itself; large or risky items get one independent reviewer task.
5. Integrate: merge reviewed commits one at a time, run combined checks, revert anything that breaks them.
6. Close: archive integrated tasks and report with evidence.

## Keeping token use down

- Long waits instead of short polling; no progress pings or acknowledgments.
- Short standalone briefs; workers never load the skill.
- Cheaper models by default (Sol / medium, Luna for mechanical work); stronger models only for the contract, hard debugging, security review, or repeated failures.
- No fan-out when the work isn't parallel.

## Claude Code

Claude Code doesn't need this skill: background agents, worktrees and completion notifications are built in. Add this to your `CLAUDE.md` instead:

```markdown
## Parallel work
For multi-part features with 2–3 independent parts (e.g. backend + Android):
1. Write the contract first (API shapes, error cases, fixtures, file ownership) and commit it on the integration branch.
2. Run each part as a background agent with `isolation: "worktree"` (max 3); each commits and reports branch, SHA and test results.
3. Review each diff and re-run its checks before merging (use a separate reviewer agent for risky code). Merge one at a time, run the full checks after each, revert on failure.
Otherwise work sequentially — don't fan out small, coupled, or single-module changes.
```

## Files

- [SKILL.md](skills/orchestrate-task/SKILL.md): flow, token rules, guardrails
- [references/task-protocol.md](skills/orchestrate-task/references/task-protocol.md): Codex tools, identity, register, gates, recovery
- [references/contracts.md](skills/orchestrate-task/references/contracts.md): contract, worker, reviewer and rework templates
- [tests/regression-scenarios.md](skills/orchestrate-task/tests/regression-scenarios.md): replay checklist

## Validation status

The regression scenarios are replay checklists, not automated tests. The lite version hasn't had a recorded live run yet.

## License

[MIT](LICENSE). Independent community skill; not an official OpenAI product.
