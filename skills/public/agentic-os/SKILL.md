---
name: agentic-os
description: Coordinate versioned cross-System capabilities. Use when the user invokes /agentic-os scout or /agentic-os pursue, or asks Agentic OS to evaluate or advance Career opportunities.
argument-hint: "scout --target <positive integer> | pursue [<opportunity-ref>...]"
---

# Agentic OS

Coordinate only the requested cross-System capability. The public surface
currently supports:

```text
/agentic-os scout --target <positive integer>
/agentic-os pursue
/agentic-os pursue <opportunity-ref>...
```

For `scout`, reject missing, repeated, non-integer, or non-positive targets. For
`pursue`, accept no arguments for automatic selection or one or more non-empty
opaque opportunity references. Reject flags, duplicate references, and every
other action. Repository roots, System bindings, profile data, throughput
targets, and native configuration are derived from installed Systems, never
accepted as public caller inputs.

## Scout contract

Scout builds one fresh, ephemeral Career profile for this invocation, reconciles
only its native delta, and invokes Career discovery and evaluation through the
canonical gateway. Load the bundled Knowledge Request from
[`resources/scout-knowledge-request.json`](resources/scout-knowledge-request.json)
and return a document matching
[`resources/scout-result.schema.json`](resources/scout-result.schema.json).

Agentic OS coordinates the calls. It does not read Knowledge provider bindings,
inspect Career implementation scripts, edit Career files, or reproduce either
System's domain rules.

### 1. Establish fresh readiness

Resolve the installed `setup-knowledge-system` and `lookup` capabilities and the
configured Career System root. Do not fetch or silently upgrade either System.

Run a fresh read-only `/setup-knowledge-system check` for `agentic-os.scout`.
Require the installed Knowledge interface, lookup, Snapshot Token validation, and
every required role in the bundled request to be ready. Record only the structured
status, capability evidence, and observation time, never personal values or
provider details.

From the Career root, invoke only:

```text
node main.mjs career-system.check/v1 --input -
```

Supply the versioned capabilities `career.profile.check/v1`,
`career.profile.reconcile/v1`, and `career.opportunity.discover/v1`. Record the
structured readiness evidence and observation time. A missing root, malformed
result, unsafe repository state, unavailable required capability, or blocked
readiness returns a capability-scoped `blocked` result. Do not guess a fallback or
invoke an internal Career script.

### 2. Build fresh profile input

Pass the bundled request unchanged to the installed automation-mode `/lookup`.
Require a valid `knowledge-system-interface/v1` snapshot whose caller and
capability are `agentic-os` and `agentic-os.scout`.

Map its current role results into a complete `career.profile.snapshot/v1` with
exactly these sections:

- `identity`
- `application_defaults`
- `opportunity_preferences`
- `positioning_and_proof`
- `communication_strategy`

Preserve every field's `value`, `absent`, or `unresolved` state, visibility,
restrictions, evidence, and provenance. Preserve uncertainty and weighted
preferences. Only explicit hard rejects become gates. Never infer a value from a
search miss, strip a qualifier, broaden the lookup, or manufacture a field.

Keep the Knowledge snapshot and Career profile only in memory or in a
permission-restricted temporary file. Remove any temporary file before returning,
including on errors. Never write a profile, snapshot, token, cache, receipt,
ledger, or resumption record in Agentic OS.

### 3. Validate drift and reconcile the native delta

Immediately before a dependent write, ask the installed Knowledge interface to
validate the opaque Snapshot Token. Never parse, compare, log, or derive meaning
from the token.

If the covered Knowledge state changed, discard the complete Knowledge and Career
snapshots. Repeat fresh Knowledge readiness, fresh Career readiness, lookup,
mapping, and token validation once. If it changes again, return `blocked` with a
scoped `persistent_drift` action. Do not combine revisions or ask a broader query.

When the token is unchanged, pass the complete Career profile through stdin to:

```text
node main.mjs career.profile.check/v1 --input -
node main.mjs career.profile.reconcile/v1 --input -
```

Use the same opaque source revision in `snapshot.revision` and
`expected_revision`. Treat `check` as read-only. Let the Career gateway own field
mapping, managed projection isolation, validation, and writes. An unresolved field
may block only its dependent capability; independent safe deltas may remain
reconciled. Never roll back a native delta or touch applications, reports,
attempts, outcomes, follow-ups, offers, observations, queues, or generated
artifacts.

After reconciliation, run a new Career `career-system.check/v1` for
`career.opportunity.discover/v1`. This post-reconcile result, not the earlier
check, authorizes scouting.

### 4. Invoke native scouting

Invoke only the canonical gateway:

```text
node main.mjs career.opportunity.discover/v1 --input -
```

Pass a versioned request containing the requested target and native continuation
references returned by the Career gateway, if any. Do not pass Knowledge provider
details, raw private profile values, or Agentic OS state.

The Career capability owns discovery, evaluation, replacement attempts, locking,
native verification, and artifact writes. Continue until exactly the requested
number of evaluations succeed or the native capability returns a terminal result.
Never invoke scan scripts, batch runners, modes, tracker writers, or other Career
internals directly.

Preserve every successful native evaluation and artifact when later work blocks or
fails. Do not delete, reset, rewrite, or roll back partial Career work. Resume only
through continuation references returned by the Career capability, never through
an Agentic OS cache.

### 5. Return the scoped result

Return `agentic-os.scout.result/v1` with capability `agentic-os.scout`. Include
fresh Knowledge and Career readiness evidence, requested and successful counts,
replacements, failures, native report and tracker references, verification,
profile reconciliation, proposed captures, and blocked actions. Reference native
artifacts instead of copying them and redact private profile values.

Use terminal statuses exactly:

- `completed`: exactly the requested evaluations succeeded and native verification
  passed;
- `blocked`: a recoverable prerequisite, required field, readiness, busy state, or
  persistent drift prevented safe progress;
- `incomplete`: native recovery paths ended after preserving partial work;
- `failed`: a schema, protocol, safety, or post-check invariant was violated.

Return one result even when the run stops before native scouting. Unresolved data
and blockers remain scoped to `agentic-os.scout`; unrelated System capabilities
remain usable. Never claim completion from counts alone without native
verification.

## Pursue contract

Pursue selects safe existing Career work, produces native plans and draft packs,
and reviews externally owned waits. Load the bundled Knowledge Request from
[`resources/pursue-knowledge-request.json`](resources/pursue-knowledge-request.json)
and return a document matching
[`resources/pursue-result.schema.json`](resources/pursue-result.schema.json).

Agentic OS coordinates only versioned contracts. Every read or update of Career
state goes through the canonical gateway. Never inspect Career trackers, reports,
pipelines, modes, templates, action files, or implementation scripts directly.

### 1. Establish fresh readiness

Resolve the installed `setup-knowledge-system` and `lookup` capabilities and the
configured Career System root. Do not fetch or silently upgrade either System.

Run a fresh read-only `/setup-knowledge-system check` for
`agentic-os.pursue`. Require the installed Knowledge interface, lookup, Snapshot
Token validation, and every required role in the bundled request to be ready.
Optional roles may be absent or unresolved without blocking the run. Record only
structured readiness evidence and observation time, never personal values or
provider details.

From the Career root, invoke only:

```text
node main.mjs career-system.check/v1 --input -
```

Require fresh readiness for `career.profile.check/v1`,
`career.profile.reconcile/v1`, `career.opportunity.select-related/v1`,
`career.opportunity.advance/v1`, and
`career.opportunity.review-waiting/v1`. A missing root, malformed result, unsafe
repository state, unavailable required capability, or blocked readiness returns a
capability-scoped `blocked` result. Do not guess a fallback or invoke a Career
internal.

If Career reports active Scout, batch, pipeline, or other conflicting work,
return `blocked` with its native busy evidence. Never infer idleness from files or
processes.

### 2. Build fresh inputs and validate drift

Pass the bundled request unchanged to the installed automation-mode `/lookup`.
Require a valid `knowledge-system-interface/v1` snapshot whose caller and
capability are `agentic-os` and `agentic-os.pursue`.

Map the current profile roles into the complete ephemeral
`career.profile.snapshot/v1` used by the Career profile capabilities. Preserve
field state, visibility, restrictions, evidence, provenance, uncertainty, and
weighted preferences. Resolve the current application-throughput target from
`job-search-strategy`; when it is genuinely absent, request the Career-owned
conservative small-batch default. Never invent a target.

Treat `communication-strategy` as optional personalization. When it is absent,
unresolved, or unavailable, pass an explicit generic-defaults selection to the
Career capabilities and continue. Never substitute remembered guidance, copy
personalization into Agentic OS, or treat missing optional personalization as a
blocker. Career owns complete generic planning defaults.

Keep the Knowledge snapshot and Career profile only in memory or in a
permission-restricted temporary file. Remove any temporary file before returning,
including on errors. Never write a profile, snapshot, token, cache, receipt,
ledger, or resumption record in Agentic OS.

Immediately before any dependent Career write, ask the installed Knowledge
interface to validate the opaque Snapshot Token. Never parse, compare, log, or
derive meaning from the token. If covered Knowledge changed, discard all derived
inputs and repeat fresh Knowledge readiness, Career readiness, lookup, mapping,
and validation once. Persistent drift returns `blocked`; never combine revisions.

When unchanged, invoke only:

```text
node main.mjs career.profile.check/v1 --input -
node main.mjs career.profile.reconcile/v1 --input -
```

Use the same opaque source revision in `snapshot.revision` and
`expected_revision`. Treat check as read-only and let Career own the safe native
delta. Never touch applications, reports, attempts, outcomes, follow-ups, offers,
observations, queues, or generated artifacts directly. Run a new
`career-system.check/v1` for all three pursue capabilities after reconciliation;
only this post-reconcile evidence authorizes pursuit.

### 3. Select eligible work

Invoke only:

```text
node main.mjs career.opportunity.select-related/v1 --input -
```

Pass a versioned request containing the optional caller-supplied opportunity
references and the resolved throughput selection. Explicit references narrow
scope but never override native eligibility, lifecycle, ownership, or
related-opportunity suppression.

Treat the native eligible set as exclusive. Preserve suppressed alternatives and
research-blocked groups exactly as references and summaries returned by Career.
Never reconstruct candidates from Career files, add suppressed work back, or use
an unattended override. Research-blocked groups remain blocked while independent
eligible groups may continue.

### 4. Advance and review through native capabilities

For eligible Agent-owned work, invoke only:

```text
node main.mjs career.opportunity.advance/v1 --input -
```

Career owns selection order, lifecycle routing, communication planning, artifact
generation, evidence checks, and safe projection writes. Agent-owned planning,
draft packs, and the internal projection that a draft now exists may proceed
without approval when the native result explicitly classifies them as safe.

For due or cold externally owned waits, invoke only:

```text
node main.mjs career.opportunity.review-waiting/v1 --input -
```

Use only confirmed native attempt and outcome evidence. The capability may
recommend waiting, draft a next route, or recommend deprioritizing or discarding.
It must not invent a reply, record an attempt, or change a factual lifecycle
state. Wait reviews do not count toward the application-throughput target.

Keep every real-world boundary approval-gated. Never submit an application, send
a message, click a final action, contact a person, record a follow-up as sent,
assert a reply or external outcome, or mark a factual real-world lifecycle change
without explicit user approval and the evidence required by Career. A draft does
not prove that an external event happened. Return required actions as human
approvals, not completed events.

If the native result surfaces a durable Knowledge signal, return it only as a
proposed capture. Any Knowledge write remains behind the installed `/capture`
approval contract and requires a fresh read before application.

Preserve every native plan, draft, safe advance, and recommendation when later
work blocks or fails. Do not delete, reset, rewrite, or roll back partial Career
work. Use only native continuation references; never create an Agentic OS cache.

### 5. Return the scoped result

Return `agentic-os.pursue.result/v1` with capability `agentic-os.pursue`. Include
fresh readiness evidence; selected, suppressed, and research-blocked references;
plans and draft packs; wait recommendations; safe Agent-owned advances; evidence
sufficiency; capacity shortfall; required human approvals; reconciliation;
proposed captures; and blocked actions. Reference native artifacts instead of
copying them and redact private profile or personalization values.

Use terminal statuses exactly:

- `completed`: every usable selected opportunity advanced safely, or a checked
  genuinely idle run found no useful work; a throughput shortfall may coexist with
  completion when every usable opportunity advanced;
- `blocked`: a recoverable prerequisite, busy state, required field, required
  capability, or persistent drift prevented safe progress;
- `incomplete`: native recovery paths ended after preserving partial work;
- `failed`: a schema, protocol, approval-boundary, or post-check invariant was
  violated.

Return one result even when pursuit stops before selection. Unresolved data blocks
only its dependent opportunity or capability. Optional personalization always
degrades to Career-owned generic defaults. Unrelated System capabilities remain
usable.
