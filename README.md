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
  `/agentic-os scout`, `/agentic-os pursue`, and the provider-neutral `/post`
  and `/tweet` authoring surfaces.
- `docs/adr/`: architectural decisions owned by Agentic OS.
- `skills/public/`: the positive public export surface.
- `skills/internal/`: committed internal skills, excluded from public export.
- `automations/internal/`: committed internal automation definitions.
- `automations/internal/social-compose/`: the canonical provider-neutral Social
  Compose release module and its non-publishing validation contract.
- `automations/internal/portfolio-refresh/`: the canonical public-safe Portfolio
  Refresh release module and its proposal-only validation contract.
- `automations/internal/job-scout/`: the canonical scheduled Job Scout release
  module, invoking `agentic-os.scout` with non-publishing, no-write validation.
- `automations/internal/job-pursue/`: the canonical scheduled Job Pursue release
  module, invoking `agentic-os.pursue` while preserving action and evidence gates.
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
