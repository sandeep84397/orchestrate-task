# Orchestrator chat UX (quiet chat)

The user watches one chat: this one. Child updates arrive here asynchronously all the
time — child turn reports, idle notices, review results, heartbeat ticks. If each one
becomes a report, the chat turns into a wall of mixed milestones and the one thing that
needs the user is lost in it. Async processing stays; async **output** does not.

**Principle: the chat shows one thing at a time. Everything else lives on the board.**

## Three lanes

Sort every event before writing anything to the chat.

| Lane | What | Where it goes |
|---|---|---|
| **Now** | Something only the user can unblock: a blocker, an approval (gate, merge, deploy), a question. | `QUESTIONS.md` / `BLOCKERS.md`; the chat as **one card** when its turn comes. |
| **Digest** | Worth knowing, needs nothing from the user: goal confirmed, review passed, findings fixed, PR opened, real-server/device test passed, merge done, bug filed, child restarted. | `FEED.md`; the chat only inside a digest. |
| **Silent** | Bookkeeping: sweep with no change, child working normally, review started, lease granted/released, `NEXT`/`GUIDE` sent. | `FEED.md` / `REGISTER.md` only. |

**Always Now:** a blocker; a child stuck on a permission prompt; a third review round on
one goal; a failed merge or integration check; a message a child hasn't acknowledged
after the `events` check; a child claiming user approval (refused and reported).
**Unsure between Now and Digest → Now.** Unsure between Digest and Silent → Silent.

## Order of cards (same as the one-question rule)

- Approvals and questions are all items in `QUESTIONS.md`, sorted as that file says
  (most work unblocked soonest). Exactly one is OPEN, shown as the current card.
- **Only a blocker pre-empts.** A new blocker parks the OPEN question and is shown at
  once (`references/pull-loop.md`, Blocker protocol); the parked question comes back
  after.
- Any other Now item arriving while a card is OPEN is queued. It does not get its own
  message; the count shows up in the next message's `Also:` line and on the board.
- When the user answers, the next message shows the next card.

## Replies to async events

Every async arrival (a child's turn report or message relayed by the host, an idle
notice, a subagent hand-back, a heartbeat tick) is processed in full — register, ledger,
FEED, messages to children. Then:

- **A blocker opened, or the OPEN card was just answered** → the standard message.
- **Anything else** → nothing visible. Where the host can mark a turn as no-change
  (claude-code `ScheduleWakeup` `noop: true`), do so. Where the turn must end with
  text, end it with one fixed line and nothing else:
  - no open blocker: `·`
  - open blocker(s): `⛔ <n> open blocker(s): M3.g4 — waiting on you`
- `chat: verbose` only: one ticker line per Digest event instead,
  e.g. `· 14:07 M2.g3 real-server test passed`.

Never answer an async event with a report, a heading per milestone, a table, or a
child's or reviewer's text. Details belong in `FEED.md`, `reviews/` and the evidence
folders.

## Standard message (fixed order)

```
⛔ Open blockers: 1 — M3.g4: the payment API returns a field the plan didn't expect (since 14:05) · others running: M1, M2
9/22 goals · for you: 3 · blocked: M3 · shipped 1/5

<ONE card>

Also: 2 more for you after this · 4 news (`digest`) · `status` for the board
```

- Line 1 (banner) only while ≥1 blocker is open. Its format is fixed, the same as in
  `references/pull-loop.md`. Never write "Open blockers: none".
- Line 2 (progress line), always one line. `for you` counts every OPEN or queued
  question/approval, including the card shown. Full form on the board.
- One card. ≤10 lines. Plain words, the user's language (Hinglish fine).
- `Also:` only when something is behind the card; each part only when non-zero.

## Cards

Shape: **decision as headline · why it matters · recommendation · how to answer.**
Goal ids are written `M2.g3` everywhere.

**Blocker card:** the format in `references/pull-loop.md` (Blocker protocol). It keeps
"I choose: <option> — because …".

**Approval card** (gate, merge, deploy):
```
✋ Merge M2 (PR #41)? Login retry with backoff.
Proof: all 4 goals reviewed · real-server test passed · suite green
Risk: low — one known old bug, unrelated, filed as #57.
I recommend: merge — nothing else depends on waiting.
Reply "ok" to merge, or "hold".
```

**Question card** (the only format for asking; QUESTIONS.md stores the same fields):
```
❓ Q4: Use branch `p0-base` as the base for M3 and M4?
Why it matters: both start from it; changing later means a merge. Unblocks: M3, M4.
I recommend: yes — it already has the two API fixes both need.
Reply "ok", or name another branch.
```

## Digest

A short news block, never inside a card message:
```
📰 Since 14:05
✅ M2.g3 passed on the real server
✅ M1.g2 review passed
🐞 New bug #57 — old drafts are never cleaned up
+3 more in FEED.md
Still waiting on you: ✋ Merge M2? — reply "ok" or "hold"
```
- At most 4 news lines, newest last; the rest folded into `+n more`.
- If a card is OPEN, the last line repeats its headline and how to answer, so the
  card never scrolls out of mind.
- Shown on `digest` / "what's new" / "kya hua", or by itself every `digest_every`
  (RUN.md, default 30m) when it has items. `chat: quiet` → only on request.
- Shown standalone only; afterwards write `digest shown <time>` in FEED and reset.

## Board (always current, outside the chat)

`<run>/BOARD.md`, rewritten on every state change (format in
`references/status-and-register.md`): open blockers, the "for you" queue, the full
progress line, one row per milestone, latest feed items. Where the host can show a file
beside the chat, open it there once at setup.

## Commands (plain messages, any time)

| User types | Gets |
|---|---|
| `status` / `board` / `blockers` | The board in the chat: open blockers first, one row per milestone. |
| `next` | The OPEN card again; if none is OPEN, the top of the queue becomes OPEN and is shown. Never skips a card. |
| `digest` / `what's new` | News since the last digest. |
| `details M<n>` | That milestone's last 10 FEED rows + current goal + STATUS `updated`. The one place SHAs and paths appear unasked. |
| `quiet` | Cards and blocker alerts only; digest on request (the news count stays in `Also:`). |
| `normal` | Default: cards, digest every `digest_every`, nothing else. |
| `verbose` | Normal + one ticker line per Digest event (for debugging a run). |

The level is stored in RUN.md (`chat: quiet | normal | verbose`).

## Copy rules

- Lead with the decision or the outcome; details after, or in a file.
- Same words everywhere: milestone, goal, blocker, approval, question, digest, board.
  Never "task", "ticket" or "job" for a goal.
- Replies are verbs: "ok", "hold", "merge", "pause M4", never a bare "yes/no" when
  the action can be named.
- No SHAs, file paths, test-class names or device setup steps in the chat unless the
  decision depends on them or the user asked (`details M<n>`).
- Errors: what happened + why + what happens next.
- Color is never the only signal: every icon has a word next to it (🔴 blocked).
- Short lines for the phone (Remote Control): ≤90 characters where possible.

## Never

- A report per child event, a heading per milestone, or a table outside `status`.
- More than one card in a message, a list of queued questions, or a digest inside a
  card message.
- "⛔ Open blockers: none".
- Repeating what the previous message said ("still waiting", "no change").
