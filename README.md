# Agentic OS

Agentic OS coordinates independently usable agent Systems through shared setup,
cross-System integrations, and automations. This repository is the public-safe
source for those definitions and policies.

It deliberately contains no runtime service, provider binding, personal state,
or synchronized compatibility manifest. Each System owns its domain behavior and
releases independently.

## Repository map

- `CONTEXT.md`: canonical constellation vocabulary and ownership rule.
- `docs/constellation.md`: low-resolution topology and dependency boundaries.
- `skills/public/`: self-contained public release modules, including
  `/agentic-os scout`, `/agentic-os pursue`, `/agentic-os upskill`, and the
  provider-neutral `/post` and `/tweet` authoring surfaces, plus
  `/orchestrate` for accepted GitHub ticket graphs.
- `skills/public/setup-agentic-os/`: the roots-only, stateless constellation
  setup composer, its fixed System contracts, and automation materialization
  tooling.
- `automations/`: the one canonical source module for Agentic OS-owned
  automation definitions and their stable-identity manifest.
- `docs/adr/`: architectural decisions owned by Agentic OS.
- `skills/public/`: the positive public export surface.
- `skills/internal/`: committed internal skills, excluded from public export.
- `scripts/package-setup-agentic-os.py`: the release-only projection that
  packages canonical automation sources into the distributed setup skill.
- `scripts/check.sh`: public-safety, ownership, and source-shape validation.
- `.github/workflows/`: clean-clone validation and independent tag releases.

## Validate

```sh
bash scripts/check.sh
git diff --check
```

## Release model

Agentic OS uses Conventional Commits and independent semantic-version tags.
Features release a minor version, fixes release a patch, and breaking changes
release a major version. Non-release commit types produce no tag.

Release versions provide source provenance only. They are not a synchronized
version of the Agentic Constellation.

The source branch never commits packaged automation copies. For a releasing
commit, CI creates a packaging commit with deterministic contents, projects
`automations/` into the setup skill, and tags that self-contained release
commit. Generated copies are therefore present in distributed skills, but there
is only one hand-edited source module.
