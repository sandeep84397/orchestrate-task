# PLAN.md template and validity checks

The orchestrator writes `PLAN.md` in the run folder after spot-checking the planner's output.
Version it (`v1`, `v2` …) in the title; on revision keep a 3-line changelog at top.

```markdown
# <Run name> — milestone plan v<N> (<plan model> <effort>, <date>)
Status: DRAFT | APPROVED <date> | SUPERSEDED by v<N+1>

## 0. Changed facts
- <fact> (VERIFIED <evidence> | ASSUMED)

## 1. Milestones
Path aliases: `A` = <abs path>, `B` = <abs path>

| ID | Name | Repo · base · branch | Est | Owns (exclusive) | Contracts |
|---|---|---|---|---|---|
| M1 | … | … · `<sha>` · `<branch>` | 1d | `A/feature/**` | produces C1 |

Frozen (orchestrator single writer): <paths>

Contracts (frozen now):
- **C1** <endpoint / symbol / schema>: <exact shape, nullability, error behaviour>

Goal rule: 3–6 goals, ≤1 day each, one evidence bundle, ≤1 user gate at the end.
Code goal = principal review → RED saved → minimal fix → GREEN → mutation.

**M1**
- M1.g1 <goal> — evidence: <bundle `g1-*`>
- M1.g2 … [gate: <what the user approves>]
Goal IDs are stable across plan versions: never renumber; a removed goal is marked
`dropped`, a new goal takes the next free number.

Testability:
| | Command | Fixtures/fakes | Device | Known-red exclusions |
|---|---|---|---|---|

## 2. Independence
- M1 vs M2: <why no block>
- Forced together: <items> (<reason>)

## 3. Shared resources
- <lease>: order <M?.g → …>, rules <…>
- Deploys: D1 <sha> → M?; orchestrator executes after the user's yes; sessions never deploy.

## 4. Merge order and integration
- Merge: <order>; later milestones `git merge` the new base + rerun suite.
- Integration (after merges, never first proof): <suite, release build, device journey, smoke>.

## 5. Questions for the user (ordered: unblocks most, soonest)
1. <question>? Recommend: <answer>. Unblocks: <M?>.

## 6. Briefs (one paragraph each)
## 7. Risks / ASSUMED / critical files
```

## Validity checks before showing the user

- [ ] Every milestone has 3–6 goals. No goal >1 day; each names one evidence bundle;
      ≤1 gate, at its end.
- [ ] No path appears in two milestones' Owns. No frozen hotspot appears in any Owns.
- [ ] Every symbol/endpoint one milestone calls from another's area is under a contract.
- [ ] Every milestone's test command runs on its own base without other milestones'
      branches and without an undeployed backend.
- [ ] Leases have an order; deploy and merge steps are gated.
- [ ] All SHAs, branches and ownership paths verified; `file:line` claims sampled; and marked VERIFIED or ASSUMED.
- [ ] Questions ordered by work unblocked, each with a recommendation.
- [ ] Every goal has a stable ID `M<n>.g<k>`; revisions list added/dropped IDs.
