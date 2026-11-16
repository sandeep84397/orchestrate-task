# Gates: production, permissions, irreversible work, merge readiness

Rules for actions that can't be taken back. Each one exists because a real run went
wrong without it. The orchestrator follows them itself and enforces them on children.

## 1. Production changes (traffic, deploys, flags, config, data)

**Policy first.** The project config's "Deploy and prod policy" must be filled before a
run starts (Phase 0): the one allowed deploy path, who runs it, what is forbidden, and
the commands that read live state. Missing → one question; nothing that touches prod is
planned or started without it. The policy is copied into every brief's never-list.

Before **every** prod-changing command, in this order:

1. **Policy check.** The command uses the allowed path. If not, don't run it: blocker,
   class `approval`. Temporary or test versions and deploys from a dev machine are
   allowed only if the policy names them.
2. **Read live state now** with the policy's read command (traffic split, serving
   versions, flags). Save it to `<run>/prod/<time>-before.txt`.
3. **Compare** with "Prod state" in REGISTER (what the orchestrator last set or saw).
   No record yet → record this read; the card says "first read". Different, and not
   from an orchestrator step → someone changed it by hand. Stop.
   Never put it "back". Ask the user (always Now): "live is X, I expected Y — keep X?"
4. **Approval card** shows `Now: <live state> → After: <target>`, the command, and how
   to undo it. The user's yes covers that one step from that live state only. If the
   state moved between the yes and the run, ask again.
5. **Run one step.** Read live state again, save `<time>-after.txt`, update "Prod
   state" in REGISTER.

No script chains several prod steps. A staged rollout is one approval per stage, each
starting again at step 2.

## 2. A permission check is an answer, not an obstacle

When a permission prompt, sandbox denial or policy block stops an action — in a child,
a subagent, or this chat:

- **The stopped session** stops that action and sets `BLOCKED`, class `access`, with
  the exact action and the denial text. It does not retry through another tool,
  command, account or route.
- **The orchestrator never does the action in its place**, and never asks another
  child or subagent to. A child's "the user approved it" is not approval.
- **Blocker card options:** the user does it themselves · the user allows it in that
  session (they answer the prompt there) · a different, policy-allowed way (named) ·
  drop the step.

## 3. Irreversible goals

Data scripts, backfills, migrations, deletes, bulk writes, anything sent to real users.
The plan marks them `[irreversible]`. The goal's plan note (`g<k>-plan.md`) must answer
this checklist **before any code**; plan-review and every review check it:

- [ ] **Selection:** the exact predicate, and proof it can't over-match: a saved sample
      of records it matches and records it must not match.
- [ ] **Dry run is the default.** Writing needs an explicit flag. The dry run prints
      scanned / matched / would change / skipped.
- [ ] **Empty result fails loudly:** zero scanned or zero matched exits non-zero with a
      message. Never "success, 0 changed" in silence.
- [ ] **Prod interlock:** refuses to write to prod without a named confirm flag plus
      the target id; prints the target before the first write.
- [ ] **Bounded:** indexed query or paged scan, a time estimate, a cap on writes per
      run, resumable, and idempotent (a second run changes 0).
- [ ] **Undo:** an export of the touched records or a reverse script; or the words
      "cannot be undone".
- [ ] **Cost:** estimated reads and writes.

Execution: only the orchestrator, under section 1, as the plan's D-steps (one for the
dry run on prod, one for the real run). When the goal is confirmed done, queue the
dry-run approval; its counts go on the real run's approval card. Where the script
allows it, run a small batch first and check it.

## 4. Merge readiness (before any merge card)

Run these checks only for the milestone **next in merge order** (the plan's order,
among milestones whose goals are done). The others wait as `goals-complete`; checking
them now would be wasted, because each merge moves the base. Show a merge card only
when all of these hold for the exact head `<sha>`:

1. **Contains the base.** `git fetch`, then
   `git merge-base --is-ancestor origin/<base> <head>`. If not: `MERGE-BASE` to the
   child; after it merges, CI, a review of the merge delta (not a second full merge
   review) and the real-system check run again on the new head. Check once more right
   before executing the merge; if the base moved after the yes, say so and re-check.
2. **CI green on that head.** No hosted CI → the card says "no CI".
3. **Reviews.** Every goal `passed`, plus one **merge review**: the whole milestone
   diff `origin/<base>..<head>` by a reviewer that saw none of the earlier rounds,
   `passed @<head>`. Later head changes need only a delta review.
4. **Real-system check:** this exact head exercised against the real backend or
   system, not fakes. Required unless the project config's merge gate says
   `real-system check: none — <reason>`. The orchestrator grants the lease and sends
   `CHECK M<n> @<sha>`; the child runs it and saves `merge-check-<sha7>.txt`. Head
   changed since → run it again. A path that can't be exercised → named on the card
   with the reason.
5. **Sections 1–3** are satisfied for anything this merge triggers.

The card's `Proof:` line states each one:
`head <sha7> · contains <base> @<sha7> · CI green · merge review passed · real-server test passed on this head`.

**Merge-ready is treated like a blocker, without jumping the queue.** When 1–5 hold
and only the user's yes is missing, the milestone becomes `merge-ready`:
- it is named in the blocker banner (`· merge waiting: M2`) on every message until
  merged, with an alert and reminders like a blocker;
- its merge card goes to the top of `QUESTIONS.md`, behind any real blocker. It never
  parks the OPEN question; it is shown as soon as that one is answered.
"hold" → milestone `on-hold`, the board shows `on hold by you`, no reminders; the card
comes back when the user says so. Only one milestone is merge-ready at a time, because
only the next in merge order is checked.
