# Domain Docs

How the engineering skills should consume this repository's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repository root.
- **`docs/adr/`** for ADRs that touch the area being explored.

If either is absent, proceed silently. Do not flag its absence or suggest creating it upfront. The `/domain-modeling` skill creates domain documentation lazily when terms or decisions are resolved.

## File structure

This repository uses the single-context layout:

    /
    ├── CONTEXT.md
    ├── docs/adr/
    │   ├── 0001-agentic-os-is-a-source-repository.md
    │   └── 0002-the-narrowest-domain-owns-a-definition.md
    └── src/

## Use the glossary's vocabulary

When output names a domain concept, such as in an issue title, refactor proposal, hypothesis, or test name, use the term defined in `CONTEXT.md`. Do not drift to synonyms that the glossary explicitly avoids.

If a required concept is absent from the glossary, reconsider whether the language belongs to this project. If it reveals a real gap, note it for `/domain-modeling`.

## Flag ADR conflicts

If output contradicts an existing ADR, surface the conflict explicitly instead of silently overriding it:

> _Contradicts ADR 0002 (the narrowest domain owns a definition), but may be worth reopening because..._
