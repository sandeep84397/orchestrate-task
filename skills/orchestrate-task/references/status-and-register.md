# STATUS.md, REGISTER.md, BOARD.md, FEED.md, BLOCKERS.md, QUESTIONS.md

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
lease: none | requested <r> (<why>, est <min>) | held <r> since <t> | released <r>   (several: separate with `;`)
next: <next concrete step>
ack: #<highest message number read>
reply: #<n> <answer to that STATUS? message> | none

BLOCKED: none

resolved:
- <id>: <answer> (one line each)
```

When blocked, replace `BLOCKED: none` with:

```
BLOCKED M<n>.g<k>-<seq>
blocked: <action>
evidence: <cmd/output/file:line/SHA>
diagnosis: <why, one line> — verified (<how>) | hypothesis
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
open blockers: none | <id> M<n>.g<k> since <time> (…) · paused by user choice: none | <M…>
progress: <done>/<total> goals (<pct>%) · waiting on you: <n> (<M.g list>) · blocked: <n> (<M list>) · shipped: <merged>/<milestones> · integration: pending | pass | fail · plan v<N> (<±delta> goals) · longest left: <M> <n> goals

| M | session (child id) | mode | branch @ sha | base | goal | state | milestone | acted | blocker | lease |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | m1-… (<child id>) | auto | `…` @ `abc123` | `def456` | 2/5 ▸g3 | red | active | g3:red @14:05 | — | — |
`mode` = the child's permission/sandbox mode at start. Add each child's status path in the
milestone notes if it isn't the run folder. `milestone` = active · goals-complete ·
merge-ready · on-hold · merged · closed. `acted` for merge readiness = `ready @<sha>`. `acted` = the goal + state + block/lease id the
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

## Messages (numbered; one open per topic per child)
| # | child | topic | sent | acked | replaces |
|---|---|---|---|---|---|
| 12 | M3 | lease device | 14:05 | 14:07 | |
cli-fallback also records the message file and when it was delivered.

## Prod state (what the orchestrator last set or read; see `references/gates.md`)
| what | value | read/set at | by | saved file |
|---|---|---|---|---|

## Heavy slots and load
slots: <used>/<max> (<holders>) · load: <1-min load average> at <time> · critical path: <M…>

## Leases
| resource | holder | since | queue (est start) | next warned (`LEASE-SOON`) |

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
  **blocked** = milestones with an open row in BLOCKERS.md (merge-ready is not counted
  here; it shows as 🟡 waiting on you). Review/red/green are just "not done".
- **shipped** = milestones merged (from the Merges log) / all milestones.
- **integration** = pending until the final check runs; the run is 100% only at `pass`.
- **longest left** = milestone with most goals not done. Milestones run in parallel,
  so this (≈ days, upper bound) is the ETA hint — not the sum, and never a date.
- Row `goal` column = done count + current goal, e.g. `2/5 ▸g3`.

## BOARD.md (orchestrator-only; the user's at-a-glance view)

Rewritten whole on every state change. `status` prints it. Plain words, no SHAs.

```markdown
# <Run name> — board · updated 14:32
⛔ Open blockers: 1 — M3 · #88 Payments · g4: the payment API returns a field the plan didn't expect (since 14:05) · merge waiting: M2
For you: 3 — OPEN: ✋ Merge M2 · #41 Login retry? · queued: ❓ Q4 base branch · ❓ Q5 board edits
9/22 goals (41%) · for you: 3 · blocked: M3 · shipped 1/5 · integration: pending

| | Milestone | Goal | Now |
|---|---|---|---|
| 🔴 | M3 Payments | 1/4 ▸g2 | blocked — waiting on you |
| 🟡 | M2 Login | 4/4 | merge waiting on you |
| 🟢 | M1 Feed | 2/5 ▸g3 | writing tests |
| ✅ | M4 Profile | 5/5 | merged |

## Latest (newest first, last 10 from FEED.md)
- 14:30 ✅ M1.g2 review passed
- 14:12 🐞 bug #57 filed — old drafts never cleaned up
```

## FEED.md (orchestrator-only; append-only event log)

One line per event, newest last; the digest and `details M<n>` read from it.

```markdown
| time | M.goal | lane | event (plain) | link |
|---|---|---|---|---|
| 14:07 | M2.g3 | digest | real-server test passed | milestones/M2/evidence/g3/ |
| 14:08 | M2.g3 | silent | review started (agent a1b2) | |
| 14:20 | M3.g2 | now | blocker B1 opened | BLOCKERS.md#B1 |
```
`digest shown: <time>` lines mark where each digest ended.

## BLOCKERS.md (orchestrator-only)

```markdown
| id | milestone.goal | class | opened | what happened (plain) | options | chosen + why | decided | closed |
|---|---|---|---|---|---|---|---|---|
| B1 | M3.g4 | contract | 14:05 | … | A/B/C | A — … | 14:20 "ok" | 14:22 |
Classes: the child classes (STATUS) plus `stuck`, `review-rounds`, `merge-failed`,
`integration`, `prod-state`. A milestone-level blocker with no goal uses `M<n>.-`.
```
Open rows are shown first on `status`, on Resume, and in the banner.

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

Asking format: the question card in `references/chat-ux.md` (exactly one OPEN).
Approvals (gate, merge, deploy) are rows here too, with the approval card.
