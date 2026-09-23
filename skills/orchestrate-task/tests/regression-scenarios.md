# `orchestrate-task` publication regression checklist

Use before publishing a skill revision. Replay fixtures in a fresh manager context; IDs below are synthetic. Assert register/message intent and reported next actions. Never call native tools for fixture IDs or claim simulated operations happened.

## Behavioral replay

| Case | Compact input | Expected observable result |
|---|---|---|
| Requester is child | Child asks parent `r/C/01`; parent answers with the verified required value. | `ANSWERED` remains pending child acceptance. Child acknowledges sufficiency and its next action; parent records `RESOLVED`. |
| Requester is parent | Parent asks child `r/P/01`; child answers; parent accepts and directs next step. | Child answer is `ANSWERED` until parent accepts. Parent records `RESOLVED`; execution of the directed step is tracked separately. |
| Partial batch | Three IDs received; one answered sufficiently, one awaits a dependency/checkpoint, one has no substantive answer. Independent artifact is ready. | Keep IDs/states distinct; resolve only accepted answer. Record owner/checkpoint for each remainder; continue independent artifact; follow up at checkpoint without premature ACK-only chatter. |
| Superseded + late execution | Request A superseded by B; late A response claims its artifact was copied to destination. | A stays terminal `SUPERSEDED`; late response cannot resolve B. Ask recipient to stop further stale-A integration; parent verifies actual destination effects and tracks execution separately. Keep B pending. |
| Blocked delivery + recovery | Open request; uncertain send; status confirms no processing; two same-ID continuation attempts at successive checkpoints show no processing; no permitted route remains. Later, transport recovers and recipient confirms receipt only. | Mark `BLOCKED_DELIVERY` with evidence, prior state, escalation owner and resume trigger; no third retry or duplicate task. On recovery reconcile same ID and record `RECEIVED` from receipt evidence only; requester acceptance remains pending (`ANSWERED`/`RESOLVED` not implied). Suspend futile polling only if no independent work remains. |
| Ordinary slow work | Recipient explicitly received request, is running with progress and gave a future checkpoint. | Keep exchange `RECEIVED`; do not classify as stalled, interrupt, reassign, or resend. Continue independent work; check at/after promised checkpoint. |
| Uncertain creation | Persisted work key/prompt marker; creation returns pending `clientThreadId`; bounded listing omits it; similar-title task has a different marker. | Preserve `creating`/uncertain identity. Reconcile with supported listings and exact marker; do not message/archive pending ID, adopt similar task, or blindly create duplicate. |
| Unknown writer + manual archive | User explicitly requests archive; child may still write and no stop control exists. | Save obligations/output/ownership; archive only requested stable task and report result honestly. State execution unknown; retain writer lock; no replacement writer. Parent objective remains active. |
| Redundant ownership | Duplicate task idle with unique note; replacement owner has not acknowledged transfer; incoming answer is unaccepted. | No automatic archive yet. Preserve note; obtain explicit transfer acknowledgment/incorporation reference and requester acceptance; reconcile affected execution, then archive with `superseded` disposition. |
| Domain-owned wait | A confirmed external prerequisite blocks one branch; another independent work item is ready. | Record source, missing prerequisite, evidence, owner, affected actions and resume trigger. Pause dependent actions only; continue independent work. Use `WAITING_EXTERNAL`/`WAITING_USER` only when no actionable work remains. |
| Fresh-context recovery | Register has reviewed output pending integration; open request has verified answer in register; first listing omits child, direct saved-ID read works; child inbox has stale exchange state. | Reuse child; do not recreate. Send evidence-backed answer using same request ID; reconcile stale copy to canonical state. Preserve only review/verification status supported by recorded evidence. Run destination checks; do not mark `integrated`/complete until incorporation and checks are verified. |
| DONE before integration | Child reports DONE and isolated tests pass; output durable but absent from destination; combined contract test fails. | Enter review then rework. Name child as fix owner and parent as integration/combined-check owner. Do not mark verified/integrated or auto-archive. |
| Same-item rework | QA child reports review-ready work; parent finds an unmet original acceptance check. | Send one evidence-backed rework brief to the same owner/task ID; wait for revised completion. Keep the work item open; create no duplicate child or active writer. |
| Independent item and token accounting | A new QA item is independent of a long-running QA task; user requests token measurement. | Compare reused-history cost with a fresh concise child, then record the chosen distinct work key/task ID and exclusive writer. Where available, capture each task's start/end cached, uncached and output tokens. Do not use shared account percentages as per-task cost or infer causal savings from different tasks. |

## Scheduler and integration smoke gates

These are real-runtime release gates. This checklist does not assert they passed.

- [ ] On a permitted disposable run, verify scheduler/heartbeat discovery and live schema before use; no hard-coded unavailable tool assumptions.
- [ ] Create one authorized monitor; capture returned ID, target, cadence, status and notification policy in the register. Reconcile uncertain create/update outcomes before retrying.
- [ ] Verify a quiet unchanged run produces no user notification; meaningful completion, failure or required action is surfaced.
- [ ] Verify monitor resumes from the exact register/run location, checks both queue directions, honors a domain-owned wait, and does not duplicate monitors or tasks.
- [ ] Verify completion pauses/deletes only the associated monitor when supported; report configured state separately from observed delivery.
- [ ] Install candidate in an isolated disposable location; confirm installed files match candidate and manifest/metadata references resolve. Do not overwrite an existing user install during smoke testing.
- [ ] Verify task creation, stable-ID resolution, messaging, status wait, grouping/title, direct-read recovery and explicit archive only against disposable real tasks with authorization.
- [ ] Verify integration gate checks durable output, accepted obligations, destination incorporation, affected combined tests, no active writer and eligible cleanup before automatic archive.
- [ ] Record exact environment, commands/actions, outcomes, limitations and evidence paths. Leave unchecked gates explicitly pending; simulated fixture results are not runtime evidence.
