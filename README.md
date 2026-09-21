# Orchestrate Task

A Codex skill for managing separate, visible Codex tasks from one parent task: divide independent work, choose models, answer questions, review outputs, integrate changes, and archive completed children.

The parent remains responsible for the final result. Children are ordinary Codex tasks tracked by this workflow, not a claim that Codex provides a native parent-child task hierarchy.

## Install

In Codex, ask the built-in skill installer:

```text
Use $skill-installer to install the skill from:
https://github.com/sandeep84397/orchestrate-task/tree/main/skills/orchestrate-task
```

It should be available on the next turn after installation. If it does not appear, restart Codex.

For manual installation, copy the entire `skills/orchestrate-task` directory into your Codex personal skills directory, normally `$CODEX_HOME/skills` or `~/.codex/skills`. Preserve `references/` and `agents/`. Inspect an existing installation before replacing it.

## Use

Choose the parent model and reasoning effort in Codex. Astra with Extra High is the suggested parent configuration when available; the skill cannot change the model of its own parent task.

```text
Use $orchestrate-task to complete this feature: [describe the outcome].
Create separate Codex child tasks where useful. Choose their models and
reasoning effort, supervise their work, integrate and verify the results,
and archive children after their outputs are accepted and integrated.
```

For example:

```text
Use $orchestrate-task to add a login flow to this project.
Agree on the API contract first, then create separate Codex tasks for
independent backend and Android work. Choose suitable models, answer child
questions, verify the combined login flow, and archive integrated children.
```

You can also ask the parent to resume an existing orchestration, inspect blockers, or archive/unarchive a specific child. Explicit task creation is required; automatic selection of the skill alone does not authorize opening new tasks.

## How it works

1. Define the outcome, acceptance checks, dependencies, and integration destination.
2. Record pending work; open child tasks only when inputs are ready.
3. Give each child clear ownership, context, checks, and a question/reporting protocol.
4. Run independent work in parallel within available capacity. Reuse tasks for corrections.
5. Resolve technical questions in the parent; escalate only decisions or blockers needing the human.
6. Review actual outputs, integrate them, and run relevant combined checks.
7. Save handoff evidence and archive verified, integrated children.

Typical lifecycle:

```text
queued -> creating -> running -> review -> verified -> integrated -> archived
                        |           |
                  needs_decision  rework
```

An explicit manual archive request can hide unfinished work, but never means the work is complete or that execution stopped. The parent records remaining obligations and keeps write ownership until execution status is known.

## Models and efficiency

The parent selects from the host's supported models and reasoning levels. Starting suggestions: Luna for bounded extraction, Terra for ordinary implementation, Sol for difficult debugging and architecture, and Astra for the hardest reasoning. These are routing suggestions, not fixed requirements or guarantees of access.

Prefer a modest active queue, concise assignments, bounded status checks, and evidence-based escalation. More tasks can reduce elapsed time while increasing total token use. Task count and concurrency are not unlimited.

## Requirements and limits

- A Codex host exposing separate-task creation, follow-up messaging, status/read, and archive controls. Tool availability and permissions take precedence over this skill.
- A writable location for a small task register and the necessary project/artifact access.
- Appropriate available models; the skill does not provision model access or modify global configuration.
- Git projects need explicit ownership and integration between worktrees; changes do not automatically appear in the parent checkout.
- Active supervision lasts only while the parent is running. Continuing later requires an explicitly requested, successfully configured automation.
- If the host prohibits separate-task orchestration, the skill reports that limitation instead of substituting subagents.
- Creating an archive does not stop execution, merge changes, delete worktrees, or grant deployment permission.

The workflow does not deploy changes, publish artifacts, or expand external permissions merely because a child asks. The original user's authorization controls scope.

## Validation status

The skill passed the bundled skill format validator, metadata checks, and reference-link checks. Seven simulated scenarios covered failed integration, uncertain task creation, child questions, overlapping changes and authorization, archived-task reuse, unavailable task controls, and manual archival of a running task.

**A live end-to-end feature run has not yet been validated.** Simulation verifies instruction behavior, not the reliability of every host's task APIs.

## Files

- [SKILL.md](skills/orchestrate-task/SKILL.md): entry point and decision rules.
- [Task protocol](skills/orchestrate-task/references/task-protocol.md): task identities, assignment contract, recovery, integration, and cleanup.
- [Codex metadata](skills/orchestrate-task/agents/openai.yaml): display name and invocation prompt.

## Contributing

Issues and pull requests welcome. Include your Codex host/version, relevant tool availability, expected behavior, actual behavior, and a minimal reproduction. Redact credentials, private project details, and sensitive task output.

Keep changes focused on observed failures and preserve the distinction between separate tasks and subagents. Do not claim live validation from simulated scenarios.

## License

[MIT](LICENSE). Independent community skill; not an official OpenAI product.
