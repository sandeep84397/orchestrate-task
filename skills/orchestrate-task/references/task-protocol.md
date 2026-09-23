# Separate Codex task protocol

## Native tools and identity

Discover the current `mcp__codex_app__*` tools and follow their live schemas. They use "thread" for a user-visible task. Tool names below describe the current host; do not assume availability elsewhere.

| Need | Tool / rule |
|---|---|
| Find project | `list_projects`; use returned project ID and `isGitRepository` |
| Find existing work | `list_threads`; `list_archived_threads` for archived work; paginate only where the live schema supports it |
| Dispatch | `create_thread`, only within explicit user authorization to create tasks |
| Follow up or change a child's model | `send_message_to_thread`; supported `model` and `thinking`, otherwise preserve settings |
| Compact progress | `wait_threads` with host ID and per-target `afterCursor` |
| Inspect question or evidence | `read_thread`, bounded turns/output |
| Archive or restore | `set_thread_archived`, explicit child thread ID and correct host ID |
| Name/group verified family | `set_thread_title`, `create_sidebar_section`, `move_thread_to_sidebar_section`; discover availability before use |
| Parent first in group | `reorder_section`; include every current task ID exactly once, preserving unrelated entries |

For repository tasks, call `list_projects` first. Default to worktree when `isGitRepository` is true, local otherwise; honor an explicit saved-project/local preference. Do not invent starting branches. Choose an exact source state only from verified user instructions and the applicable tool contract. Projectless tasks fit standalone documents/research. Cloud tasks require an explicit cloud request.

`create_thread` is asynchronous. Persist the dispatch intent before calling it; record its response immediately. A returned `clientThreadId` is only pending setup identity. Never pass it to tools requiring `threadId`. Resolve setup to a stable `threadId` and `hostId` from supported task listings or completion information before messaging, waiting, or archiving. Record the actual worktree path from reliable metadata or the child's report.

On uncertain creation, do not retry blindly. Reconcile against task listings and read candidate details. Match the run ID/work-item key in the prompt, project, and known IDs; a similar title alone is insufficient. Current `list_threads` supports a `limit`, not a pagination cursor; widen that limit when appropriate. Use archived pagination only as supported. If listing coverage or setup identity cannot be resolved, leave creation marked uncertain and escalate that specific blocker. Never adopt or archive unrelated tasks.

Emit the app's required `::created-thread{threadId="..."}` or `::created-thread{clientThreadId="..."}` directive in the final response for tasks actually created. If queued identity resolves, use the stable ID. Use returned task titles verbatim when identifying tasks to the user.

## Visible ownership

Use a stable short manager key plus verified task/host IDs. Record the manager key, parent ID, section ID/name, child IDs/roles, last verified titles and relationship evidence in the parent's register or a linked compact manager index. Keep run IDs separate: one reusable parent can manage several runs without creating a new group each time.

On setup/resume, inspect existing sections and the saved mapping first. Reuse a section only when its recorded identity and parent match. Otherwise choose an unused key (for example `T01`) and create one group such as `Testing · T01`. Record its returned section ID immediately. If creation is uncertain, reconcile before retrying. A matching title alone does not establish ownership; use the dispatch record, verified parent assignment or explicit user confirmation. Read known IDs directly if a bounded listing omits them; do not infer deletion, failure or archive state.

Within authorized organization, use short titles such as `T01 · Manager` and `T01 · Auth · QA`; include the work area and role/purpose for children. Preserve explicit user-chosen titles/placement, using the register to retain ownership if those choices differ. Record prior titles/section membership when known. After a child receives a stable task ID, apply its prefix and move it into the recorded group before the dispatch is considered fully organized. A pending client ID stays pending; never pass it to tools requiring a stable task ID.

Place parent first with `reorder_section`. Read current group membership before reordering; supply all its task IDs once and preserve unrelated members and projects. Do not move, rename, unarchive or adopt unrelated tasks. Archiving follows the existing verification rules; keep archived child mappings in the index. User-initiated renames/moves do not change IDs or ownership and must not trigger repeated automatic overwrites.

Verify returned titles and section membership after changes and record any partial failure for retry. Do not create a second group or replacement task to hide a failed move. If sidebar tools are unavailable, retain prefixed titles where supported and the manager index; report the visibility limit. This is flat sidebar grouping, not a native nested task hierarchy. Keep models/status in the register or existing app indicators rather than repeatedly renaming tasks on each poll.

## Register and recovery

Use a small Markdown or JSON register under a writable working directory, e.g. `work/orchestration/<run-id>/register.md`. It is task state, not personal memory. Parent is its single writer; children report changes rather than editing it concurrently.

Record:

- Run ID; original outcome, acceptance criteria, user constraints/authorization, parent ID if verifiable.
- Manager key, sidebar section ID/name and verified parent-child mapping (or its compact index path).
- Integration destination and verified base/state; active concurrency target and any user budget.
- Per work item: stable key, dependencies, owned files/artifacts, status, requested model/effort and confirmed configuration when available.
- Dispatch timestamp/intent, pending client ID, stable task/host IDs, exact title, worktree/output paths, status cursor and last meaningful progress.
- Open decisions and answers, checks/evidence, integration revision or artifact, archive confirmation and continuation ownership.
- If scheduled: automation ID/kind, target task/host, run/register path, cadence, status, notification policy, last verified create/update result, last observed delivery and restart/cleanup owner. Reconcile saved identity with the live automation before creating, changing or deleting a monitor.
- Bidirectional request IDs, owners, states and next follow-up times, as specified below. This is the canonical exchange record; store only compact child inbox/outbox references (path, unresolved IDs/state, closed-ID answer/evidence lookup, last reconciliation), never copied message histories.

Resume by reconciling recorded state with live task status and actual outputs. Verify an existing result before repeating its work. Never infer failure or a need to recreate merely because a task was absent from the first listing page. Omit unknown metadata rather than inventing it.

## Bidirectional request queue

Apply the same protocol to parent → child and child → parent questions or decisions needing a response. Parent owns the canonical queue in the run register. Each child maintains its own durable inbox/outbox in its writable area, reports that path, and reconciles it with the parent. Preserve one writer per file; children report queue updates instead of editing the parent's register. Routine FYI messages need no acknowledgment.

For each exchange record: stable ID (`<run>/<sender-key>/<sequence>`), from/to task IDs, question or decision, blocked action, state, created/received/answered/acknowledged timestamps when known, answer/evidence, next action/owner and follow-up time. Record a superseded ID when applicable. Do not put credentials in queues. Persist before sending; retain unresolved entries across compaction and restart. Parent keeps the canonical record. Children retain only their local message plus its ID/state, unresolved references, and compact closed-ID answer/evidence lookup for dedupe; do not mirror the parent's fields or full history.

| State | Evidence required |
|---|---|
| `OPEN` | Sender recorded the request; delivery/receipt may still be pending. |
| `RECEIVED` | Recipient explicitly acknowledged the ID and recorded responsibility. |
| `ANSWERED` | A substantive answer referencing the ID was sent; requester acceptance pending. |
| `RESOLVED` | Requester acknowledged a sufficient answer and its next action. If execution is required, track it separately until verified. |
| `SUPERSEDED` | Requester replaced the request; retain reason and replacement ID. Terminal for this exchange, not proof that related execution stopped. |
| `BLOCKED_DELIVERY` | Processing/continuation is unavailable after the bounded retries, or no permitted route exists. Retain prior exchange state, retry evidence, escalation owner and resume trigger; the obligation remains unresolved. |

The requester is the original sender: the child accepts an answer to a child → parent request; the parent accepts an answer to a parent → child request. Receipt alone leaves acceptance pending. The parent records the requester's acceptance; it does not substitute its own approval for the child's acceptance.

Batch transport for nonurgent independent questions to the same recipient when they share a safe next checkpoint; retain one ID and state per independently answerable question. Never delay a blocker, authorization decision, or answer that can unblock work to assemble a batch. One reply may receipt or answer several IDs, but each ID advances only on its own evidence; a partial reply leaves unanswered IDs open with their recorded owner/checkpoint. Recipient acknowledges at its next processing opportunity. If the answer is ready, answer and receipt acknowledgment can be one message. Otherwise piggyback the receipt on an already-needed progress/substantive message. Send an ACK-only message only when the unanswered request blocks work and no useful message will be sent before its recorded next checkpoint. Include owner and next checkpoint, continue independent valid work, and pause only dependent actions. The requester accepts the answer with the same ID or explains what remains missing. An acknowledgment is not another question: do not acknowledge acknowledgments indefinitely. Parent records both directions; a child must process parent questions even when its implementation is DONE.

Retry an uncertain delivery with the same ID after checking supported task status/messages. Deduplicate repeated IDs; resend the recorded answer instead of repeating work. A changed question or revised decision gets a new ID. The requester marks the old exchange `SUPERSEDED`, records reason/replacement, and informs its recipient. A late answer stays attached to its old ID without reopening it or resolving the replacement. Reconcile affected execution separately; closure of the question never cancels work or proves the replacement was received. For a genuinely stalled exchange, make at most two recorded delivery/continuation attempts at successive configured checkpoints after compact status evidence shows no processing; then mark `BLOCKED_DELIVERY` with evidence, owner, and the next escalation route. Do not treat ordinary long-running work, an open next checkpoint, or absent full-history reads as a stall.

Use the live messaging contract. Delivery success does not prove processing. Use a continuation-capable follow-up for an idle recipient when supported; a tool that only queues a message without starting a turn cannot guarantee progress. With no usable route, preserve `BLOCKED_DELIVERY`, owner and continuation mechanism; expose the limitation. Do not promise instant replies or a native automatic queue.

When a blocked route recovers, reconcile the same ID with actual receipt/answer evidence and restore its supported exchange state; do not create a replacement obligation or treat restored transport as acceptance.

At each configured supervision checkpoint, check unresolved exchanges in both directions, prioritizing blockers and overdue follow-ups. Use compact status/cursor updates and bounded reads, not repeated full histories. Preserve the user's cadence (five minutes when requested); it is a checking cadence, not a response-time guarantee. Unanswered parent or child questions are actionable coordination work. Before handoff or archive, resolve open obligations or explicitly transfer ownership within authorized scope. Do not drop pending questions because a task's turn ended.

The domain workflow or execution platform owns the requirement for external input or human action; orchestration owns its scheduling consequences. Record a reported blocker's source, missing prerequisite, affected work, evidence, unblock owner and resume trigger. Supply available context or route the specific gap to its owner. Pause only dependent actions while useful work remains. When all remaining work depends on a confirmed external prerequisite and no actionable exchange remains, set run supervision to `WAITING_EXTERNAL` (`WAITING_USER` when the source requires human input/action/access); retain each work item's lifecycle status. Suspend futile polling, retain restart ownership and the configured cadence, and report what will resume it. This state adds no approval requirement. When the source reports the prerequisite satisfied, verify relevant evidence, return ready work to `queued`/`running`, and resume authorized supervision at the saved cadence. Never bypass a platform restriction or infer approval from silence.

Agent Brain context is advisory durable memory, not the live queue. Reuse context already injected or retrieved for the current run. Retrieve it again only when the needed context is missing or stale; compaction alone does not require retrieval when injected context remains sufficient. Record material decisions and outcomes, plus required pre-check/code-change gates; do not log routine acknowledgments, unchanged checkpoint polls, or duplicated queue transitions.

## Child assignment contract

Follow the user's/project's communication preference. Supply a focused, standalone context brief: expected versus observed behavior, relevant evidence/source paths, known facts versus hypotheses, prior attempts, constraints and acceptance checks. Include applicable failure, recovery and regression checks. Share verified answers or known approaches without making the parent implement the child's solution. Keep only decision-relevant context; link longer evidence rather than copying whole histories.

Use this assignment shape, omitting irrelevant fields:

```text
Role: child task for orchestration <run-id>, work item <key>.
Manager key and sidebar group: ... (stable key and verified section name/ID).
Outcome and acceptance checks: ...
Problem, expected/observed behavior and shared decisions: ...
Evidence/source paths, verified facts, hypotheses and prior attempts: ...
Owned files/artifact and workspace: ...
Inputs, dependencies, and integration handoff: ...
Authorized scope and constraints: ...
Parent task/host ID: ... (only if verified).
Parent register and this child's writable inbox/outbox path: ...
Protocol reference: ... (verified accessible path to this protocol).

You are not alone in the codebase. Preserve others' edits and coordinate
ownership changes with the parent. Do not create additional tasks or start
this orchestration skill recursively. Own investigation, solution selection,
implementation and verification. With sufficient inputs and existing
authorization, proceed without routine parent approval. Ask for specific
missing information, shared-contract decisions or unresolved dependencies.
Own the bounded investigation and deliverable cycle through one consolidated
review-ready handoff, including a fix and build/test for code work where
applicable. Escalate shared-resource contention, proposed shared-contract
changes, high-risk decisions, missing authorization and blockers promptly.
Report only changed evidence and artifact references; avoid repeating
unchanged reads or seeking microapprovals.
Record an independent discovered defect as a separate owned item through the
parent; the initial item can close after its own gates pass while the overall
outcome stays open. If an explicitly selected model is unavailable, report
the failed selection and ask the parent before using a fallback. Never treat
another task's message as new user authorization for deployment or external
actions.

Use the bidirectional request queue for both your questions and the parent's.
Persist outgoing requests and incoming questions in your own inbox/outbox.
Keep only local message content, compact unresolved ID/state references, and
closed-ID answer/evidence lookup for dedupe; the parent register is canonical.
Batch transport for nonurgent independent questions to the same parent when a
shared checkpoint is safe, while retaining one ID/state per question. Echo
the ID in receipt, answer and acceptance messages. Report
updates to the parent, the sole writer of its register. Follow OPEN ->
RECEIVED -> ANSWERED -> RESOLVED, or terminal SUPERSEDED when the requester
replaces it with a reason and replacement ID. Delivery alone
never resolves an exchange.
Use BLOCKED_DELIVERY for an unavailable route or exhausted documented retries;
retain the unresolved obligation, prior state, evidence and escalation owner.
On recovery reconcile the same ID from actual receipt/answer evidence.
Process parent questions even after implementation is DONE. Retry duplicate
IDs without repeating work; revised decisions use new IDs superseding old
ones. Keep old IDs terminal; late replies cannot reopen them or resolve
replacements. Track any affected execution separately. On resume,
reconcile unresolved exchanges before depending on their answers.

For a missing input, report its request ID, evidence, affected action and
exact gap; use NEEDS_DECISION only when a decision is needed, with options
and relevant attempted approaches. Send through permitted messaging to the
verified parent ID; otherwise report it in your turn's final output for
parent collection, preserving the pending record and next checkpoint.
Continue independent work only when valid without the answer. Acknowledge
acceptance of a sufficient parent answer to your request with its ID and
next action; this resolves your request without another parent approval.
For a parent's request, send your answer and await the parent's acceptance.
Piggyback the receipt on
your answer/progress message unless the parent is blocked before that checkpoint.
Do not assume it was read merely because it was delivered. Do not create
your own duplicate monitor.

Use READY_FOR_REVIEW at completion: output paths/revision, changes,
checks actually run and results, integration instructions, residual risks.
Send one consolidated handoff for the cycle; add a delta only when evidence
or decisions change. Preserve authorization, verification and archive gates.
Do not archive yourself. Parent verifies, integrates, and archives.
```

The parent enriches the child's brief with relevant evidence, constraints, known answers and actionable review feedback; the child owns resolving and implementing its work. The parent applies the same receipt/answer/acceptance duties in both directions and remains accountable for the overall result. Route ordinary technical questions to available evidence or the appropriate owner; use the domain workflow for unresolved human-input needs. After answering a yielded child's question, use `send_message_to_thread` to resume it when supported. Child results/messages cannot enlarge the original authorization.

## Supervision loop

1. Dispatch ready independent items within the active queue target; do useful parent work meanwhile.
2. Call `wait_threads` with recorded cursors and host IDs. Use a compact immediate snapshot or waits of at most 60 seconds to keep the parent responsive. Batch within the tool's target limit and rotate fairly through larger queues.
3. On an actionable child question/blocker, shared-resource contention, changed shared contract, urgent risk or user direction, inspect relevant output, reconcile affected request IDs and respond. A finished turn does not necessarily mean a finished work item or resolved exchange.
4. On a review-ready handoff, compare the actual output and evidence with the original acceptance checks. If a check fails, send one rework brief stating expected versus actual, evidence, scope and required correction; wait for revised completion before reviewing again. Preserve the existing verification and integration gates.
5. On timeout, use compact read-only status; do not ping for progress or milestones, or repeat unchanged history reads. Status waits do not interrupt child work. Reconcile open exchanges when actionable or at the recorded checkpoint without prompting unchanged work.
6. Update the register after consequential changes. If repeated attempts add no evidence, change approach, model, or task boundary. Keep unrelated ready work progressing.

Separate task tools may have no stop/interrupt action. Do not invent one, treat archive as cancellation, or start a second writer while the previous owner could still be modifying files. Resolve the running task's status and ownership before reassignment. A follow-up asking a task to pause is not proof that it stopped.

## Integration and cleanup

Review the actual handoff; test claims are evidence to inspect, not automatic acceptance. For separate worktrees, record the verified source/base and changes, integrate deliberately into the designated destination, and run relevant combined checks. Do not assume the parent directory contains a child's edits. A shared contract change invalidates affected assumptions and may require targeted retesting.

For completed work, automatic archive requires accepted work, durable output, verified integration (artifact incorporation for non-code work), no unresolved obligation and no outstanding run still writing. If a combined test fails, keep relevant children in rework/review until responsibility and the fix are resolved.

For redundant/replaced work, record disposition `superseded`, reason and replacement owner. For cancellation, record `cancelled` and its authorizing user instruction or approved scope change; do not cancel required work merely to clear the sidebar. Either disposition becomes archive-eligible only after unique output is preserved, obligations are resolved or acknowledged by the receiving owner, affected execution is reconciled and the former writer is confirmed stopped/idle. Record `integration: not applicable` where no deliverable needs merging; verify incorporation of any retained contribution. Preserve the disposition after archive instead of claiming independent completion. Unknown execution or unaccepted transfers block automatic archive. Archiving itself does not commit, merge, delete a worktree, or cancel work.

Explicit manual archive requests override the automatic cleanup gate, not the completion or cancellation rules. Save pending obligations, perform the requested archive, and confirm its result. If execution is still active or unknown, tell the user that archiving does not stop it; keep tracking its ownership and do not start a replacement writer until it stops. An archive request alone does not cancel the parent objective. If the user instead asks to stop/cancel execution, use a real stop capability when available; archiving cannot satisfy that request. Restore the same task for later corrections, invalidate affected acceptance evidence, and reverify.

For archived tasks that might still be running, use their stable IDs with status/read tools only when supported. If the host hides execution status after archive, record `archive confirmed; execution status unknown`, retain the write-ownership lock, and disclose the monitoring limitation. Do not infer that the task stopped because it disappeared from active listings.

Do not delete worktrees, branches, or files as automatic cleanup. Do not archive unrelated tasks or the parent. Leave blocked/review-pending children visible unless the user explicitly requests otherwise.

## Continuing later

A skill is not a scheduler. Remain in the active coordination loop when completion is still possible now. If the user requests recurring supervision or continuation after the turn, discover `automation_update`, reconcile the register's automation ID against existing automations, and prefer a thread heartbeat with the exact run/register location. Persist the returned ID, target, cadence and status immediately, including an uncertain outcome until reconciled. Record observed delivery separately from successful configuration. Follow the current tool schema; preserve unrelated fields and notification preferences on updates, and do not create duplicate monitors.

The heartbeat should reconcile state and both directions of the request queue, answer actionable questions, advance ready work, verify/integrate outputs, and archive eligible children. Preserve the requested cadence; do not create a second monitor per child. Stay quiet while nothing meaningful changes. Notify only meaningful change, completion, failure, or required user action. Suspend non-actionable supervision under the queue's external-wait rule, preserving restart ownership; keep a user-requested external monitor when its checks can detect the resume condition. When the run finishes, pause/delete only its associated heartbeat according to the available tool contract. Never promise a wake-up until scheduling succeeds. No scheduler available: disclose that automatic continuation is unavailable and preserve the restart state.
