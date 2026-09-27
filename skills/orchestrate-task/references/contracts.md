# Templates

Drop fields that do not apply. Keep each one readable in a single pass.

## Contract file (committed on the integration branch)

```markdown
# Auth API — v1
Producers: B1 · Consumers: A1

POST /v1/auth/login
  Request: { "email": string, "password": string }
  200: { "accessToken": string, "expiresIn": int }
  401: { "error": "INVALID_CREDENTIALS" }
  429: { "error": "RATE_LIMITED", "retryAfter": int }

Examples (runnable): valid → 200; wrong password → 401; 6th try in 1 min → 429
Fixtures: contracts/fixtures/login-200.json, -401.json, -429.json
Ownership: backend/auth/** → B1 · app/feature/login/** → A1 · build files, DI → lead
Changelog: v1 initial
```

Never edit a version after it has been sent to workers; add a new version.

## Worker brief

```text
Role: worker for run <R1>, item <B1>. Do not orchestrate or create tasks.
Outcome: <one sentence>
Acceptance checks: <runnable list>
Contract: <path> v<1>, base commit <sha>. Do not edit it; report CONTRACT_CHANGE.
You own: <globs>. Ask the lead before touching anything else.
Workspace: <worktree/branch>. Commit your work before reporting.
Context: <paths, known facts, prior attempts>
Authorized: edit owned files, run builds/tests. Not: push, deploy, publish.
Decide technical details yourself. Use fixtures if your dependency isn't ready.
No progress updates. Send exactly one final report:
  READY_FOR_REVIEW: branch, SHA, worktree path, checks + results, assumptions, risks
  NEEDS_DECISION: Q-id, options, recommendation, what is blocked
  CONTRACT_CHANGE: change, reason, impact (finish unaffected work first)
  BLOCKED: prerequisite, owner, unblock trigger
```

## Reviewer brief (large or risky items only)

```text
Role: reviewer for run <R1>, item <B1>. You did not write this. Do not modify it.
Acceptance checks: <same list>
Contract: <path> v<n>
Under review: worktree <path>, commit <sha>. Run everything there, not in the lead's checkout.
1. Run the checks yourself. 2. Verify every contract rule and error case. 3. Read the diff for bugs, security, missing tests, edits outside owned files.
Reply: PASS + evidence, or FAIL + per check: expected, actual, evidence, smallest fix.
An unrun check is not a pass.
```

## Rework brief

```text
Rework <B1>, round <2>. Failed: <check> — expected <x>, actual <y>, evidence <cmd/output>.
Fix only this, on contract v<n>. Commit, then send READY_FOR_REVIEW.
```
