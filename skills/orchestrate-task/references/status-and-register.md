# STATUS.md, REGISTER.md, QUESTIONS.md

Children write only their own STATUS.md and evidence dir, at the adapter's **status path**
(the run folder on claude-code; `<worktree>/.orchestrate/` on codex and cli-fallback).
Everything else lives in the run folder and is written only by the orchestrator.

## STATUS.md (child-owned; orchestrator seeds it at setup)

```markdown
# M<n> <name>
updated: <ISO time>
branch: <actual branch> @ <sha>   base: <sha>
goals (plan v<N>): M<n>.g1 ✓ · M<n>.g2 ▸ · M<n>.g3 · M<n>.g4
goal: <goal id> <goal title>
state: not-started | plan-review | red | green | mutation-ok | review | waiting-gate | paused | done
prep: none | drafting g<k+1> | done g<k+1> | <PREP task + output path>
evidence:
- g1: <evidence dir>/g1-red.txt, g1-green.txt, g1-mutation.txt
lease: none | requested <r> (<why>, est <min>) | held <r> since <t> | released <r>
next: <next concrete step>
reply: <answer to the orchestrator's latest STATUS? message, or none>

BLOCKED: none

resolved:
- <id>: <answer> (one line each)
```

When blocked, replace `BLOCKED: none` with:

```
BLOCKED M<n>.g<k>-<seq>
blocked: <action>
evidence: <cmd/output/file:line/SHA>
need: <one exact question or approval> — recommend: <answer>
class: contract | lease | cross-milestone | review | frozen-file | technical | approval | product | access
meanwhile: <same-goal step that doesn't depend on the answer> | STOPPED
```

On `UNBLOCK <id>` or `GUIDE <id>` the child moves the block to `resolved:` and continues.
`goals:` is the child's copy of its goal IDs; it changes only on a `PLAN` message.

## REGISTER.md (orchestrator-only)

```markdown
# <Run name> register
run folder: <abs> · skill: <SKILL_DIR abs> · platform: <adapter> · group: <id or prefix> · orchestrator: <title>
heartbeat: <interval> · last tick <time> · open question: Q<k> | none
paused: none | <blocker id> since <time> (every child paused until the user decides)
progress: <done>/<total> goals (<pct>%) · waiting on you: <n> (<M.g list>) · blocked: <n> (<M list>) · shipped: <merged>/<milestones> · integration: pending | pass | fail · plan v<N> (<±delta> goals) · longest left: <M> <n> goals

| M | session (child id) | mode | branch @ sha | base | goal | state | milestone | acted | blocker | lease |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | m1-… (<child id>) | auto | `…` @ `abc123` | `def456` | 2/5 ▸g3 | red | active | g3:red @14:05 | — | — |
`mode` = the child's permission/sandbox mode at start. Add each child's status path in the
milestone notes if it isn't the run folder. `milestone` = active · goals-complete ·
merge-asked · merged · closed. `acted` = the goal + state + block/lease id the
orchestrator last acted on, and when; a flag equal to it is already in hand.

## Goal ledger (orchestrator-confirmed; source of truth for progress)
One row per goal across all milestones, in PLAN order. IDs are stable (`M<n>.g<k>`).
| goal | title | state | commit | evidence | review | gate | started | done |
|---|---|---|---|---|---|---|---|---|
| M1.g1 | … | done | `abc123` | ✓ red/green/mut | passed r1 @abc123 | n/a | 11-14 09:10 | 11-14 13:55 |
| M1.g2 | … | active:review | `bcd234` | ✓ | running <agent id> since 14:20 @bcd234 | pending | 11-14 14:00 | |
| M1.g3 | … | queued | | | | | | |
States: queued · active:<STATUS state> · unconfirmed (records disagree) · done · dropped (plan revision).
Review: `running <agent id> since <t> @<sha>` · `findings r<n>` · `passed r<n> @<sha>`; reports in `reviews/`.
`started` = when `NEXT` was sent; `done` = when confirmed. Actual durations from these
two columns are what the orchestrator re-plans with (lease order, when to ask a gate
question early, which milestone is the long pole).

## Pending messages (cli-fallback: queued while a child's turn is running)
| child | message file | queued | delivered |

## Leases
| resource | holder | since | queue |

## Answers log
- <time> Q3 → "<user's words>" → relayed to M2, M4

## Merges / deploys / frozen edits
- <time> M2 merged `<sha>` → <branch> (approved Q7)

## Close-out summary
```

### Progress line (recompute on every register update)

Answers "how far, what's stuck, what's on me" at a glance. No weighting, no partial
credit — goals are capped at ≤1 day, so a plain count is honest enough.

- **done** = goal-ledger rows in state `done` (orchestrator-confirmed: evidence,
  review passed, gate approved if gated). `unconfirmed` does not count.
- **total** = goal-ledger rows not `dropped` (= goals in the current PLAN.md). When a plan revision (or an
  integration failure) adds/removes goals, show `plan v<N> (+n goals)`; never re-base
  silently.
- **waiting on you** = goals in `waiting-gate` + open user questions blocking a goal.
  **blocked** = milestones with a `BLOCKED` block. Review/red/green are just "not done".
- **shipped** = milestones merged (from the Merges log) / all milestones.
- **integration** = pending until the final check runs; the run is 100% only at `pass`.
- **longest left** = milestone with most goals not done. Milestones run in parallel,
  so this (≈ days, upper bound) is the ETA hint — not the sum, and never a date.
- Row `goal` column = done count + current goal, e.g. `2/5 ▸g3`.

## QUESTIONS.md (orchestrator-only)

Ordered queue. Re-sort on every new item: most work unblocked soonest (blocked or
waiting goals, then critical-path milestones), then age. Exactly one item may be `OPEN`.

```markdown
| # | status | question | recommend | unblocks | source | asked / answer |
|---|---|---|---|---|---|---|
| 1 | OPEN | Approve plan v1? | yes | all | plan | 14:00 |
| 2 | queued | Use `<branch>` at `<sha>` as the base for M3, M4? | yes | M3, M4 | plan | |
| 3 | answered | … | … | … | M2.g4-1 | 13:10 → "no" |
```

Asking format (exactly one per turn):

> **Q<k>: <question>?** Recommend: <answer> — <one-line why>. Unblocks: <M…>.
