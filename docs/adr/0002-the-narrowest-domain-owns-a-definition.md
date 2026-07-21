# ADR 0002: The narrowest domain owns a definition

Status: Accepted

## Context

A coordination repository can become a duplicate source of truth if it absorbs
System vocabulary, provider configuration, domain workflows, or operational state.

## Decision

The narrowest domain that fully explains a definition owns it. Agentic OS owns a
definition only when correct behavior requires cross-System knowledge or
constellation-wide policy.

Agentic OS references versioned public System contracts. It does not copy System
domain documentation, provider bindings, personal facts, operational records, or
implementation internals. A fixed Implementation remains owned and released by its
own repository.

## Consequences

- Ownership is explicit and reviewable.
- System changes do not require mirrored documentation updates here.
- Integrations fail at their own boundary without disabling unrelated Systems.
- New source modules must be self-contained without embedding another repository.
