---
name: agentic-os
description: Coordinate versioned cross-System capabilities. Use when the user invokes /agentic-os scout or asks Agentic OS to scout and evaluate Career opportunities from fresh Knowledge context.
argument-hint: "scout --target <positive integer>"
---

# Agentic OS

Coordinate only the requested cross-System capability. The public surface
currently supports:

```text
/agentic-os scout --target <positive integer>
```

Reject missing, repeated, non-integer, or non-positive targets. Reject every other
action until its contract is bundled by this module. Repository roots, System
bindings, profile data, and native configuration are derived from installed
Systems, never accepted as public caller inputs.

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
