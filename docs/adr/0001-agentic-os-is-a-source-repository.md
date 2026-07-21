# ADR 0001: Agentic OS is a source repository

Status: Accepted

## Context

Cross-System setup and automation need one public owner. Giving that owner live
control-plane responsibilities would make independently usable Systems depend on
shared runtime infrastructure.

## Decision

Agentic OS is a public-safe source and specification repository. It owns shared
setup composition, cross-System integrations and automations, low-resolution
constellation documentation, and distribution policy.

It does not run a daemon or scheduler, host a shared database, keep installation
state, select System implementations at runtime, or maintain a synchronized
constellation release manifest. Runtime harnesses and materialization targets are
bindings outside the repository.

## Consequences

- Every System remains independently usable and releasable.
- Setup derives current state from live System contracts and materializations.
- Agentic OS releases describe only Agentic OS source provenance.
- Coordination definitions can later ship as self-contained release modules.
