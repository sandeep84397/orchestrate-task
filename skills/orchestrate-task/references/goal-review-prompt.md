# Goal completion review (every goal, holistic)

Every goal gets this review when the child sets `state: review`, code goals and non-code
goals alike, with RUN.md's `review` role: op `subagent` in the background, or a
read-only CLI run on another platform (`references/models.md`). Start it only after
the evidence files check out (pull-loop decision table). A goal can't be confirmed done without `REVIEW … passed` bound to its head SHA.

**Holistic** means the reviewer judges the goal against the whole run, not just the
diff: does this goal move the milestone toward its done-definition, without breaking a
contract, another milestone, or the final integration? Give it the material, not your
conclusion. Fill every `<…>`. Prepend the project config's communication-style line.

---

Read-only review: do not edit files, run builds, push, or message anyone. Return the
report as your answer.

## The goal
<M<n>.g<k>: goal text from PLAN v<N>> · evidence expected: <bundle>
Milestone done-definition: <from the brief>

## The change
- Repo / worktree: <abs path> · branch `<branch>` · head `<sha>`
- This goal's diff: `git -C <worktree> diff <previous confirmed goal sha>..<head>`
  (first goal: the milestone base). Milestone context: `git diff --stat <base>..<head>`.
  Files another milestone changed (arrived via `MERGE-BASE`) are not this goal's.
- Round <r>: <first review | re-review — previous findings below; review
  `git diff <last reviewed sha>..<head>` and whether those findings are fixed | fresh
  full review — you have not seen earlier rounds; review the whole goal diff | merge
  review — the whole milestone diff `origin/<base>..<head>`, as if seeing it first>
- Marks: <[irreversible] [high-risk] | none> · background cost line: <from PLAN | none>
- Evidence: <evidence dir>/g<k>-red.txt, -green.txt, -mutation.txt (+ others)

## The whole picture
- Plan: <run folder>/PLAN.md (milestones, ownership, frozen list, contracts C1…, goals)
- Ledger + other milestones' state: <run folder>/REGISTER.md
- Other milestones touching related areas: <M?: branch @ sha, what they changed>
- Previous review findings on this milestone: <list or none>

## Check, in this order
1. **Goal met.** The change does what the goal says — no less, no unasked extras.
2. **Tests prove it.** RED fails for the right reason; GREEN passes; mutation shows the
   new tests fail without the fix. Tests check behaviour, not implementation details.
   Gaps in edge cases the goal implies.
3. **Architecture.** Layering, dependency direction, external deps behind interfaces,
   per the project's architecture rules (principal persona).
4. **Boundaries.** Only owned files touched; no frozen file edited; consumed contracts
   faked, not imported; produced contracts additive only.
5. **Cross-milestone and integration risk.** Anything that will conflict or behave
   differently once other milestones merge; anything the final integration check must
   cover because of this goal.
5b. **Real behaviour and cost.** Do the fakes match the contract's real sample, and
   would this pass against the real system? New or changed background work (calls,
   polling, prefetch, re-downloads): how often, and does it match the plan's line?
   `[irreversible]`: every item of the checklist in `<SKILL_DIR>/references/gates.md`
   §3 answered and tested: selection can't over-match (sample saved), dry run by
   default, empty result fails loudly, prod interlock, bounded/resumable/idempotent,
   undo, cost.
6. **Milestone trajectory.** Does this goal leave the next goals in a good position?
   Anything the orchestrator should tell the child in its next `NEXT`?

## Report (≤400 words)
`verdict: passed | findings`
Findings: numbered, severity (blocker / should-fix / nit), `file:line`, concrete fix.
Only blockers and should-fixes stop the goal; nits ride along.
`for the orchestrator:` cross-milestone or integration notes, and guidance for the
next goal (goes into `NEXT`, not to the child as a finding).
