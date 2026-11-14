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
   `merged`, `closed` are never flagged as idle, and neither is a child the user chose
   to pause. A new `BLOCKED` is always flagged.
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
| `BLOCKED` | **Blocker protocol** (below): only that milestone waits; blocker card to the user right away; banner until fixed; act on the user's answer. |
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

## Blocker protocol (only the blocked milestone waits; the user always sees it)

The user watches the orchestrator chat, not the children. Every blocker must be
impossible to miss there, and only the blocked milestone waits for the fix; the rest
of the run keeps going.

**What counts as a blocker:** a `BLOCKED` block in any STATUS; a child that is stuck or
errored and doesn't recover after one nudge; a goal failing its third review round; a
`GATE` rejection that changes scope; a failed merge or integration check. Normal waits
(lease queue, review in progress, gate question pending) are not blockers.

1. **Hold only the blocked milestone.** It already waits (`meanwhile: STOPPED` or only
   same-goal steps). Other milestones keep working. If another milestone would build on
   the same problem (same contract, same frozen file, its next goal needs the answer),
   don't pause it on your own: list it in the card as "also at risk" and offer pausing
   it as an option.
2. **Investigate** with the whole picture: PLAN, contracts, the blocked child's STATUS
   and evidence, recent events, other milestones' state and code, the answers log.
   Ask the `principal` or `review` role if it's hard. Work out real options.
3. **Show the blocker card right away**, in the user's language and plain words (no
   jargon; explain any unavoidable term in a few words). A blocker card outranks normal
   questions: if a normal question is OPEN, park it (re-ask it after) and show the card.
   Several blockers → one card at a time, oldest first; the others wait in the banner.

   ```
   ⛔ Blocker <id> — Milestone M<n> (<name>), goal M<n>.g<k>
   What happened: <1–3 plain sentences: what the child was doing and what stopped it>
   What is waiting: M<n> only · Still running: <M…> · Also at risk: <M… and why | none>
   Options:
     A. <option> — good: <…> · cost/risk: <…>
     B. <option> — good: <…> · cost/risk: <…>
     C. <option, if a real third one exists>
   I choose: <A> — because <plain reason tied to the run's goal, risk and time>
   Reply "ok" to go with <A>, or pick another option / tell me what to do.
   ```
   Options must be genuinely different (not one option plus straw men). The chosen one
   is the orchestrator's honest recommendation.
4. **Keep it visible until it's fixed** (see "Keeping blockers visible" below).
5. **Act on the answer:** apply the chosen option. Usually that means `UNBLOCK` or
   `GUIDE` to the blocked child, a contract/PLAN update, a frozen-file edit, or a new
   goal. Log it in the answers log, quoting the user, and close it in `BLOCKERS.md`.

## Keeping blockers visible (orchestrator chat)

- **Banner on every message.** While any blocker is open, every orchestrator message,
  tick reports included, starts with one line:
  `⛔ Open blockers: <n> — M3.g4: <plain one-liner> (since 14:05) · others running: M1, M2, M4`
- **Status board.** On `status` (or `blockers`), and in every tick report that changes a
  milestone's state, show one row per milestone:
  `M | goal | state | blocker`, with 🔴 for blocked, 🟡 waiting on you, 🟢 working,
  ✅ done.
- **BLOCKERS.md** in the run folder: every card, open or closed, with the decision and
  when it was taken. On Resume, open blockers are shown first.
- **Alerts when the user may be away:** a notification as the card opens (claude-code:
  `PushNotification`, which reaches the phone when Remote Control is on; codex: the
  thread/automation notification; cli-fallback: `osascript -e 'display notification'`
  or `notify-send`). Unanswered: remind after 30 min, then hourly, until answered.
  claude-code also pins this chat and marks it unread while a blocker is open.

How the options are usually shaped, by blocker class:

| class | typical options |
|---|---|
| contract | Additive contract change (update PLAN.md, tell every producer/consumer) · move the work into one milestone · fake it and defer. Breaking changes always need the user. |
| lease | Reorder the lease queue · revoke from the current holder · run the step without the resource (fixture). |
| cross-milestone | Answer from the other milestone's state · give a contract + fake · re-sequence goals. Never "import the other milestone's code". |
| review | Fix the findings as stated · the `principal` role settles the architecture dispute · split the goal. |
| frozen-file | Orchestrator edits the frozen file on `<run>-frozen` (pushing it needs the user's yes) then `MERGE-BASE` · work around it inside owned files. |
| technical | A concrete approach (`GUIDE`) · narrow the goal · spike in a separate goal. |
| approval / product / access / other | The decision itself, with the orchestrator's recommendation. |

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
PAUSE <blocker id>: finish the command you're running, start nothing new, set state: paused, end your turn (only when the user chose to pause a milestone)
RESUME <blocker id>: <one-line outcome> — continue where you stopped
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
- Bury a blocker: while one is open, the banner leads every message.
- Message a child that is working normally without a reason from the table.
- Implement milestone code, run a child's full suite, or merge/deploy without a yes.
