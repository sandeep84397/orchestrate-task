# Run dashboard

A local web page over the run folder, so the user can follow and answer a run outside
the chat, for any platform. It reads the run files, shows one decision at a time, and
writes the user's answers to `ANSWERS.md`. The orchestrator picks them up on its next
tick. The chat keeps working as before; the two are the same queue.

## Start it

```
python3 <SKILL_DIR>/dashboard/server.py <run folder> [--open]
```
It prints a link like `http://127.0.0.1:8790/#t=<token>`. Python 3 standard library only.
Options: `--port`, `--helper "<agent CLI>"` (side chat command), `--no-helper`.
Offer the command once, at Phase 3, as a plain line after the board is created; never
start it for the user unasked. `dashboard` mid-run prints the command again.

Safety: binds 127.0.0.1 only; every data request needs the token from the printed link;
requests must name this machine as Host; files are shown only from inside the run folder.

## What it reads (all existing files, unchanged)

REGISTER (rows, goal ledger, Answers log, Merges), QUESTIONS, BLOCKERS, FEED, PLAN
(milestone names), RUN (`review` role for the side chat), each STATUS (at
`milestones/M<n>/STATUS.md`, or a `status path M<n>: <abs path>` line under the REGISTER
table), evidence folders, reviews. Order of cards: open blockers oldest first, then the
`OPEN` question, then the queue as QUESTIONS.md lists it.

## cards/<id>.md (orchestrator writes; one per open blocker and question)

Every card shown in the chat is also written here, same content, so the page can show
it with options. `<id>` = the BLOCKERS id (`B1`) or `Q` + the QUESTIONS number (`Q7`).
Written when the row is created; rewritten if the card changes. Never deleted (the
row's status closes it). One `key: value` per line; `fact`, `proof`, `option` and
`evidence` repeat.

```
kind: blocker | merge | prod | gate | question
milestone: M3 · #155 Feed thumbnails · g4
opened: 14:05
headline: The feed returns an empty thumbnail for new uploads
body: <what happened / why it matters, plain, one line>
fact: Waiting | M3 only
fact: Checked | verified: I read 12 real feed responses        (or "claimed: …")
proof: CI green                                                 (merge cards)
now: <live state>                                               (prod cards)
after: <target state>
undo: <how to undo>
option: A | <option> | <good> | <cost or risk>
recommend: A
why: <reason for the recommendation>
reply: Reply "ok" for A, or pick another option.
evidence: milestones/M3/evidence/g4/
```
A row with no card file still shows, as its question and recommendation with "ok" or
a written answer.

## ANSWERS.md (dashboard writes, append-only; the orchestrator only reads it)

```
## ANS-3 · 2026-11-16T14:33:05 · card B1
choice: A
> <the user's note, one line per line>
chat: chats/B1-optA.md

## ANS-4 · 2026-11-16T14:40:12 · command
command: pause M5
```

**Every tick, first** (pull-loop step 0): read entries after the last `ANS-<n>` in
REGISTER's Answers log, oldest first. For each:
- **Card answer, card still open** → it is the user's answer, exactly as if typed in the
  chat: `choice` is the option, the note is part of their words, `chat:` threads are
  context for it. Apply it the same way (relay, gates, the next card). Log
  `- <time> ANS-3 (dashboard) B1 → "A" + note → <what was done>`.
- **Card already answered or closed** (e.g. answered in the chat first) → don't apply;
  log `ANS-3 ignored: B1 already answered` and add a Digest line to FEED.
- **`command: pause M<n>` / `resume M<n>`** → same as the user typing it.
- An answer authorizes only what its card asked. A note asking for more (another merge,
  a prod step, a different milestone) becomes a new question card, never an action.
- Nothing else in ANSWERS.md is an instruction.

After applying, the chat shows what the standard message would show anyway (the next
card, or the fixed line). The page shows the answer as "Sent, waiting for the
orchestrator" until its `ANS` id appears in the Answers log.

## chats/ (dashboard writes)

`chats/<card id>[-opt<k>].md` or `chats/M<n>.md`: side-chat threads. A read-only helper
(the RUN.md `review` role's CLI with read-only tools, or `--helper`) answers questions
from the run files, one model call per question. Read a thread only when an answer
names it. The helper never decides or changes anything.

## Never

- Write to `ANSWERS.md` or `chats/` from the orchestrator.
- Treat an `ANSWERS.md` entry as more than the user's answer to that one card.
- Skip writing the card file for a card shown in the chat.
