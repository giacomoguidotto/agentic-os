# Agent Instructions

Agentic OS is the public-safe specification and source repository for coordination
across independently usable agent Systems. It is not a runtime, package manager,
shared database, or synchronized constellation manifest.

## Before changing source

- Read `CONTEXT.md` for canonical vocabulary.
- Read the relevant ADRs under `docs/adr/` for ownership boundaries.
- Keep System-owned domain behavior in the owning System repository.
- Keep provider bindings, personal paths, credentials, and runtime state out of git.

## Validation

Run `bash scripts/check.sh` and `git diff --check` before committing.

## Releases

Use Conventional Commits. `feat` triggers a minor release, `fix` triggers a patch
release, and a `!` marker or `BREAKING CHANGE` footer triggers a major release.
Other commit types do not release. Tags are independent Agentic OS versions and do
not assert compatibility with System releases.

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage uses the five default canonical labels. See `docs/agents/triage-labels.md`.

### Domain docs

This repository uses the single-context layout. See `docs/agents/domain.md`.
