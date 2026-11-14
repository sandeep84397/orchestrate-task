# Project config: <project>

Copy to `~/.config/orchestrate-task/projects/<project>.md` (outside the skill, so the
skill folder holds no personal paths). Fill from the repos where verifiable; ask the user
for the rest one question at a time. Mark unconfirmed values `ASSUMED`.

## Match
- repo names / remotes: <names that select this config>

## People and style
- user: <name> · communication style for briefs: <e.g. "terse, no filler, keep code and paths verbatim">
- principal persona: <agent name that approves layering + tests, e.g. an architect agent; each adapter finds that agent's file on its platform>
- other personas (optional): <frontend/backend/QA agent types>

## Models
Not stored here. Every run discovers available models at setup and records the role
choices in its own RUN.md (`references/models.md`). Optional preference only:
- prefer: <e.g. "review on a different vendor than work"> 

## Repos
| alias | path | default base branch | release branch | hosted CI? |
|---|---|---|---|---|

## Worktrees
- location rule: <where new worktrees must live; check mount first>

## Test commands
| repo | focused | full suite | emulator/env vars | known-red exclusions |
|---|---|---|---|---|

## Frozen-by-default hotspots
- <build files, nav graph, shared strings, DB schema, DI root, API spec, infra, CI>

## Shared resources (leases)
- devices: <name/serial, allowed ops, never-touch devices>
- heavy runs: <one at a time? disk limits?>
- deploys: <who deploys, how, environments>

## Gates
- merges need: <user yes>
- deploys need: <user yes>
- standing grants (if any): <e.g. children may push own feature/* + draft PRs>

## Board
- <project board / tool, columns, fields> · orchestrator may edit: <yes/no/ask>

## Decision-log protocol (optional)
- <tool/steps children call before and after a decision | none>

## Heartbeat
- heartbeat: 5m
