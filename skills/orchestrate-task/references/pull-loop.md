# Manager loop (Phase 4)

The orchestrator is the **manager** of every milestone chat. It holds the whole
picture — PLAN.md, the goal ledger, every child's state, every contract, every open
question — and decides each child's next move: hand the next goal, unblock, guide,
review, grant, or escalate to the user. Children never message it; it pulls. Some hosts
relay a child's turn report anyway: that is a trigger to sweep, never proof of anything.

**Keep every child busy.** A child whose milestone still has work should not sit idle
waiting on the orchestrator. Detecting that and handing it its next piece of work is
the first job of every tick.

## Triggers
- Heartbeat tick (op `heartbeat`, interval from RUN.md, default 5m).
- An idle notice from a child (where the adapter supports one) or a host wake-up.
- Every user answer (after relaying it).
- A background review agent finishing.
- A child's turn report or message relayed by the host (claude-code relays them).
Each is processed fully; what reaches the chat is decided by `references/chat-ux.md`.
If the previous tick is still in progress, skip; the next trigger picks it up.

## Tick procedure
1. **Sweep every child (cheap, two calls, every tick).**
   - Op `sweep` → for each registered child id: running or idle, last activity.
   - `grep -H -E '^(goals|goal|state|prep|lease|updated|ack|BLOCKED M)' <every child's status path>`
     → refresh **every** milestone row in REGISTER.md and the `acked` column of Messages.
   - Machine load (`uptime`, or the platform's equivalent) → REGISTER "Heavy slots and load".
2. **Flag** a child only when something needs the orchestrator **and** it differs from
   that row's `acted` key (goal + state + block/lease id). Equal = already in hand; skip
   unless its timeout below has passed. Milestones in `goals-complete`, `merge-asked`,
   `merged`, `closed` are never flagged as idle, and neither is a child the user chose
   to pause. A new `BLOCKED` is always flagged.
   Flags: idle while active · stuck · plan-review requested · review requested ·
   review result ready · BLOCKED · lease requested · lease queue head due soon ·
   gate answer arrived · plan/goal-list mismatch · message unacked for 2 ticks
   while the child is idle ·
   pending message for an idle child (cli-fallback) · next-in-merge-order milestone
   with goals done (not `on-hold`).
3. **Handle every flagged child, one at a time**, idle/stuck first, then blocked,
   review, lease, gate. Finish one child's decision, message and register update
   before the next. Slow work (review agents) runs in the background — start it,
   record it, move on.
4. **Record** every event in `FEED.md` with its lane (Now / Digest / Silent,
   `references/chat-ux.md`); rewrite `BOARD.md` if any state changed.
5. **Show** only what `references/chat-ux.md` allows: a new blocker → its card at once
   (it parks the OPEN question); the OPEN card just answered → the next card. Anything
   else → nothing visible (or the one fixed line when the turn must end with text). A
   digest goes out only when it is due.

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
| review result: passed | Pass only if the review rules below are met (fresh full review after behaviour-changing fixes; second reviewer for `[high-risk]`). Else start the missing review. |
| review passed, goal ungated | Ledger → `done`. One message: `REVIEW … passed @<sha>` + `NEXT` (or the last-goal row). |
| review passed, goal gated | Message `REVIEW … passed @<sha>`; child sets `waiting-gate`. Queue the gate question at once. |
| review result: findings | Message `REVIEW … findings`. Third findings round on one goal → the `principal` role decides, still stuck → escalate. |
| gate answered | Approved → ledger `done`, one message `GATE … approved` + `NEXT` (or `DONE`). Rejected → `GATE … rejected — "<words>"`; the child treats the words as findings and redoes from tests. |
| `BLOCKED` | **Blocker protocol** (below): only that milestone waits; blocker card to the user right away; banner until fixed; act on the user's answer. Class `access` (a permission check stopped it) → `references/gates.md` §2: nobody does it in the child's place. |
| lease requested | Grant if free and next in order; else queue with an estimated start. `heavy`: grant while slots used < max and load < the project's limit; over the limit, only milestones on the critical path (the one with most goals left first). |
| lease queue head due in ≤15 min | `LEASE-SOON <r> est <time>` to it, once. |
| idle mid-goal | From op `events`: `GUIDE` if it's stuck, else a one-line nudge with the next step. |
| idle, prep done, waiting | Parked — fine. Move that child's pending question/review to the front. |
| last goal `done`, milestone next in merge order | Milestone → `goals-complete`. Merge readiness (`references/gates.md` §4): gaps → `MERGE-BASE` / start the merge review / `LEASE` + `CHECK`. Backlog waits until after the merge. |
| last goal `done`, not next in merge order, approved backlog left | `NEXT` the first backlog goal it can start now (milestone stays `active`); when its turn to merge comes, it finishes the current backlog goal, then readiness. |
| last goal `done`, not next, no backlog | `DONE` (stand by). Milestone → `goals-complete`; readiness runs when it is next in merge order. |
| `[irreversible]` goal confirmed | Queue the dry-run approval (the plan's D-step, `references/gates.md` §3). |
| §4 holds, only the user's yes missing | Milestone → `merge-ready`: banner mention, alert, merge card at the top of the queue behind real blockers (`references/gates.md` §4). After merge → `merged`, `closed` (op `complete`); the next milestone in merge order starts readiness. "hold" → `on-hold`, not flagged again until the user says so. |
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
`GATE` rejection that changes scope; a failed merge or integration check; live prod
state that differs from what the orchestrator recorded. Normal waits (lease queue,
review in progress, gate question pending) are not blockers. A merge-ready milestone
is shown in the banner but queued like a question (`references/gates.md` §4).

1. **Hold only the blocked milestone.** It already waits (`meanwhile: STOPPED` or only
   same-goal steps). Other milestones keep working. If another milestone would build on
   the same problem (same contract, same frozen file, its next goal needs the answer),
   don't pause it on your own: list it in the card as "also at risk" and offer pausing
   it as an option.
2. **Investigate** with the whole picture: PLAN, contracts, the blocked child's STATUS
   and evidence, recent events, other milestones' state and code, the answers log.
   Ask the `principal` or `review` role if it's hard. Work out real options.
   **Check the child's diagnosis before building on it.** Read the code or logs it
   cites, or have a read-only subagent try to disprove it. Behaviour that is on purpose
   (a comment, a flag, a test that asserts it) is not a bug. The card says
   `verified by <how>` or `the child's claim, not checked`.
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

- **Banner on every message.** While any blocker is open, every standard message and
  digest starts with this line (never when none is open; quiet event replies use the
  short fixed line in `references/chat-ux.md`):
  `⛔ Open blockers: <n> — M3 · #88 Payments · g4: <plain one-liner> (since 14:05) · merge waiting: M2 · others running: M1, M4`
- **Board.** `BOARD.md` lists open blockers first, then one row per milestone
  `M | goal | state | blocker`, with 🔴 blocked, 🟡 waiting on you, 🟢 working, ✅ done.
  `status` (or `board`, `blockers`) prints it in the chat; it is not repeated in event
  replies.
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
| access (permission check) | The user does it themselves · the user allows it in that session · a policy-allowed alternative (named) · drop the step. Never "the orchestrator does it instead". |
| prod state changed | Keep the live state (update the record) · the user says what it should be. Never "put it back" on your own. |
| approval / product / other | The decision itself, with the orchestrator's recommendation. |

## Reviews (every goal, holistic)
**When a goal passes.** Reviews that look only at the delta after fixes keep missing
problems, so:
- Round 2+ is a delta review (the delta plus the earlier findings), except the first
  round whose fixes touch non-test code: that round is a **fresh full review** instead
  (a new reviewer, no earlier rounds, the whole goal diff). At most one per goal; it
  counts as a round for the third-round rule.
- `[high-risk]` goals: round 1 has two independent reviewers, each on the whole diff,
  neither seeing the other's report; both must pass or their findings merge into one
  list. Later rounds have one reviewer.
- Before the merge card, one **merge review** of the whole milestone
  (`references/gates.md` §4).

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
idle notice where the adapter supports it. **Number every message** `#<n>` (one counter
per run) and log it in REGISTER "Messages" with its topic. The child writes `ack: #<n>`
in STATUS when it reads it. **One open message per topic per child:** don't send a
second on the same topic until the first is acked; if it must change, send
`#<n> replaces #<m>: …`. A reply that answers an older number than the latest on that
topic is stale: don't act on it. A message usually reaches a child only at its next
step or turn, so
**bundle**: `MERGE-BASE`, `PLAN` and reviewer notes ride along with the next `NEXT`
unless they affect the active goal. Unacknowledged after 2 ticks in which the child
was idle (a busy child acks at its next step) → op `events`; still nothing → queue a question (a child may be
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
LEASE-SOON <resource> est <time>: prepare (build, steps) so you can start the moment it's granted
CHECK M<n> @<sha>: run the real-system check on this exact head (lease granted separately); save merge-check-<sha7>.txt
MERGE-BASE <repo> <sha>: merge at your next goal boundary, rerun focused tests
PLAN v<N> M<n>: goals now <id: title list>; changed: <what>
STATUS? <specific question> — answer in STATUS reply:
```
Every message starts with `#<n>`; combine parts with ` + `, e.g.
`#14 REVIEW M3.g2: passed @abc123 + NEXT M3.g3: …`.

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
- Write a report per child event, a section per milestone, or more than one card in a
  message; echo a child's or reviewer's report into the chat (`references/chat-ux.md`).
- Message a child that is working normally without a reason from the table.
- Implement milestone code, run a child's full suite, or merge/deploy without a yes.
- Change anything in prod without `references/gates.md` §1 (policy, live read, compare,
  one approved step); run a multi-step prod script.
- Do an action a permission check stopped in a child, or ask another session to.
- Decide on a child's diagnosis without checking it.
- Show a merge card before `references/gates.md` §4 holds.
