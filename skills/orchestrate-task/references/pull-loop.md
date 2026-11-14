# Manager loop (Phase 4)

The orchestrator is the **manager** of every milestone chat. It holds the whole
picture — PLAN.md, the goal ledger, every child's state, every contract, every open
question — and decides each child's next move: hand the next goal, unblock, guide,
review, grant, or escalate to the user. Children never message it; it pulls.

**Keep every child busy.** A child whose milestone still has work should not sit idle
waiting on the orchestrator. Detecting that and handing it its next piece of work is
the first job of every tick.

## Triggers
- Heartbeat tick (op `heartbeat`, interval from RUN.md, default 5m).
- An idle notice from a child (where the adapter supports one) or a host wake-up.
- Every user answer (after relaying it).
- A background review agent finishing.
If the previous tick is still in progress, skip; the next trigger picks it up.

## Tick procedure
1. **Sweep every child (cheap, two calls, every tick).**
   - Op `sweep` → for each registered child id: running or idle, last activity.
   - `grep -H -E '^(goals|goal|state|prep|lease|updated|BLOCKED M)' <every child's status path>`
     → refresh **every** milestone row in REGISTER.md.
2. **Flag** a child only when something needs the orchestrator **and** it differs from
   that row's `acted` key (goal + state + block/lease id). Equal = already in hand; skip
   unless its timeout below has passed. Milestones in `goals-complete`, `merge-asked`,
   `merged`, `closed` are never flagged as idle.
   Flags: idle while active · stuck · plan-review requested · review requested ·
   review result ready · BLOCKED · lease requested · gate answer arrived ·
   plan/goal-list mismatch · pending message for an idle child (cli-fallback).
3. **Handle every flagged child, one at a time**, idle/stuck first, then blocked,
   review, lease, gate. Finish one child's decision, message and register update
   before the next. Slow work (review agents) runs in the background — start it,
   record it, move on.
4. **Report** to the user only on change, one line:
   `[14:05] 9/22 goals (+1) · M3 g2 done → g3 red · you: 2 waiting · blocked: M4 · shipped 1/5`
5. **Ask:** if no question is OPEN and the queue is non-empty, ask the top one.

### Liveness
- **Idle** = not running, milestone `active`, and its current goal not confirmed.
  Op `events` (last 5) to see why, then act (decision table).
- **Stuck** = running, last activity >10 min old, and STATUS `updated` unchanged.
  Op `events` (last 5) to classify:
  - permission prompt → the user must answer in that session; queue a question.
  - error / context exhausted → **restart** (below).
  - long build or test run → fine; set `acted` so it isn't re-read for 30 min.
- **Restart:** op `restart child` in the child's existing worktree (a new worktree
  can't check out a branch already checked out), prompt = original brief + "RESTART:
  ignore 'Start now with g1'. Goals <ids> are confirmed done. Continue <current goal
  id> from STATUS.md." Update the child id in the register.

## Decision table

| Child state | Orchestrator does |
|---|---|
| `plan-review` requested | Run the `principal` role on `<evidence dir>/g<k>-plan.md` (+ layering rules); reply `PLAN-REVIEW M<n>.g<k>: approved \| changes — …`. While goal k is in review, also run it on the child's prep note for g<k+1>, so `NEXT` can say "plan note approved". |
| `review` requested | Check evidence files first (exist; red fails, green passes, mutation fails; commit on branch). Missing → message the gap, no review. Present → start the review (below), ledger `review: running`. |
| review result: passed, goal ungated | Ledger → `done`. One message: `REVIEW … passed @<sha>` + `NEXT` (or `DONE` if last goal). |
| review result: passed, goal gated | Message `REVIEW … passed @<sha>`; child sets `waiting-gate`. Queue the gate question at once. |
| review result: findings | Message `REVIEW … findings`. Third findings round on one goal → the `principal` role decides, still stuck → escalate. |
| gate answered | Approved → ledger `done`, one message `GATE … approved` + `NEXT` (or `DONE`). Rejected → `GATE … rejected — "<words>"`; the child treats the words as findings and redoes from tests. |
| `BLOCKED` | Resolve, guide, or escalate (below). |
| lease requested | Grant if free and next in order; else queue. |
| idle mid-goal | From op `events`: `GUIDE` if it's stuck, else a one-line nudge with the next step. |
| idle, prep done, waiting | Parked — fine. Move that child's pending question/review to the front. |
| last goal `done` | Milestone → `goals-complete`; queue the merge question → `merge-asked`; after merge → `merged`, then `closed`. |
| STATUS `goals:` ≠ PLAN | `PLAN` message. |
| working normally | Nothing. Don't interrupt. |

A goal is **done** in the ledger only when the orchestrator's own records agree:
evidence verified, `REVIEW passed` bound to the current head SHA, and the gate approval
in the answers log if gated. If the head moves after a pass (rework, `MERGE-BASE`),
re-review the delta before confirming.

## Blocked: resolve, guide, or escalate
Use the whole picture first — PLAN, contracts, other milestones' state and code, the
answers log, review notes. The user is the last resort.
1. **Resolve** — contract, lease, cross-milestone, review dispute, frozen-file:
   decide and send `UNBLOCK`.
2. **Guide** — technically stuck (test won't pass, unclear approach, design choice in
   scope): read the code, check what other milestones did, ask the `principal` role or a
   `review`-role agent if hard. Send `GUIDE` with a concrete approach.
3. **Escalate** — approval, product decision, access, anything irreversible, or a
   blocker that survived two `GUIDE`s: queue a question with a recommendation, then
   relay the answer as `UNBLOCK`, quoting the user.

| class | default path |
|---|---|
| contract | Resolve. Frozen contract change: additive only, update PLAN.md, `UNBLOCK` every producer/consumer. Breaking → escalate. |
| lease | Resolve. |
| cross-milestone | Resolve. Never tell a child to import another milestone's code; give the contract and a fake. |
| review | Resolve; architecture dispute → the `principal` role; still stuck → escalate. |
| frozen-file | Resolve: edit on `<run>-frozen`; shared-base push needs the user's yes; then `MERGE-BASE`. |
| technical | Guide. |
| approval / product / access / other | Escalate. |

## Reviews (every goal, holistic)
Use `references/goal-review-prompt.md` with RUN.md's `review` role: op `subagent`
in the background on this platform, or a read-only CLI run when `review` names another
platform (`references/models.md`).
- Record in the ledger: `review: running <agent id> since <t> @<head sha>`. Never start
  a second one while that is running. No result after 20 min → start one replacement;
  on resume treat `running` as lost.
- Diff = previous confirmed goal's SHA → head (not the milestone base), plus the
  milestone `--stat` for context. Re-reviews (round 2+) get only the delta since the
  last reviewed SHA plus the previous findings.
- Save the returned report to `<run>/reviews/M<n>.g<k>-r<seq>.md`. Its
  `for the orchestrator:` notes go into the next `NEXT`, or into another milestone's
  next message if they concern that milestone.

## Messages to children (the only formats the orchestrator sends)

Send with op `message`. For `NEXT`, `GUIDE`, `REVIEW`, `GATE`, `DONE`, ask for an
idle notice where the adapter supports it. A message usually reaches a child only at
its next step or turn, so
**bundle**: `MERGE-BASE`, `PLAN` and reviewer notes ride along with the next `NEXT`
unless they affect the active goal. Unacknowledged after 2 ticks (STATUS not
reflecting it) → op `events`; still nothing → queue a question (a child may be
holding messages for the user's approval, or its CLI session may have failed).

```
NEXT M<n>.g<k>: start — <goal text from PLAN v<N>> — guidance: <contracts, what other milestones did, reviewer notes, pitfalls> — plan note: approved | not yet reviewed
PLAN-REVIEW M<n>.g<k>: approved | changes — <list>
GUIDE M<n>.g<k>-<seq>: <approach, files, steps, contract, fake>
UNBLOCK M<n>.g<k>-<seq>: <answer, incl. updated contract text if any>
PREP M<n>.g<k+1>: <specific prep task> — no product code, no RED run, no commits
REVIEW M<n>.g<k>: passed @<sha> | findings — <blockers + should-fixes>
GATE M<n>.g<k>: approved | rejected — "<user's words>"
DONE M<n>: all goals confirmed — stand by for merge; no further work
LEASE <resource>: granted | revoked — stop at the next safe point and mark released
MERGE-BASE <repo> <sha>: merge at your next goal boundary, rerun focused tests
PLAN v<N> M<n>: goals now <id: title list>; changed: <what>
STATUS? <specific question> — answer in STATUS reply:
```
Combine with ` + ` in one message, e.g. `REVIEW M3.g2: passed @abc123 + NEXT M3.g3: …`.

## Leases
- Child sets STATUS `lease: requested <resource> (<why>, est <min>)`.
- Grant when free and next in order: `LEASE <r>: granted`; record holder + since.
- Child sets `lease: held <r> since <t>`; when done, `lease: released <r>`.
- Re-grant only after `released` or the holder's session is dead. Past the estimate:
  `STATUS?`, or `LEASE <r>: revoked` if another milestone has waited longer than that.

## Reconcile (on resume and after every plan revision)
Re-read PLAN.md and every STATUS.md; rebuild the goal ledger, keeping the
orchestrator's own review/gate records; treat `review: running` as lost; send `PLAN`
for any goal-list mismatch; note corrections in REGISTER.

## Never in a tick
- Ask a second question while one is OPEN.
- Message a child that is working normally without a reason from the table.
- Implement milestone code, run a child's full suite, or merge/deploy without a yes.
