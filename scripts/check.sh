#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

fail() {
  printf 'check: %s\n' "$1" >&2
  exit 1
}

path_is_prohibited() {
  case "$1" in
    knowledge-system|knowledge-system/*|*/knowledge-system|*/knowledge-system/*|\
    mastery-system|mastery-system/*|*/mastery-system|*/mastery-system/*|\
    career-ops|career-ops/*|*/career-ops|*/career-ops/*)
      return 0
      ;;
    provider|provider/*|*/provider|*/provider/*|\
    providers|providers/*|*/providers|*/providers/*|\
    bindings|bindings/*|*/bindings|*/bindings/*|\
    runtime|runtime/*|*/runtime|*/runtime/*|\
    server|server/*|*/server|*/server/*|\
    daemon|daemon/*|*/daemon|*/daemon/*)
      return 0
      ;;
    constellation.yml|*/constellation.yml|\
    constellation.yaml|*/constellation.yaml|\
    constellation.json|*/constellation.json|\
    constellation.toml|*/constellation.toml|\
    release-manifest.*|*/release-manifest.*)
      return 0
      ;;
    local|local/*|*/local|*/local/*|*.pem|*.key|*.p12)
      return 0
      ;;
  esac

  return 1
}

required_files=(
  AGENTS.md
  CONTEXT.md
  README.md
  CONTRIBUTING.md
  LICENSE
  docs/constellation.md
  docs/adr/0001-agentic-os-is-a-source-repository.md
  docs/adr/0002-the-narrowest-domain-owns-a-definition.md
  skills/public/post/SKILL.md
  skills/public/post/agents/openai.yaml
  skills/public/tweet/SKILL.md
  skills/public/tweet/agents/openai.yaml
  scripts/bump-version.sh
  .github/workflows/check.yml
  .github/workflows/release.yml
  skills/public/domain-reconnaissance/SKILL.md
  skills/internal/setup-project/SKILL.md
  skills/internal/setup-project/agents/openai.yaml
  skills/internal/setup-project/resources/repository-setup.md
  automations/internal/repo-pr-ci-repair-sweep/automation.toml
  automations/internal/repo-pr-ci-repair-sweep/prompt.md
)

for path in "${required_files[@]}"; do
  [[ -s "$path" ]] || fail "required source is missing or empty: $path"
done

for skill in post tweet; do
  skill_file="skills/public/$skill/SKILL.md"
  metadata_file="skills/public/$skill/agents/openai.yaml"

  grep -Eq "^name: $skill$" "$skill_file" \
    || fail "public skill name is invalid: $skill"
  grep -Eq '^description: .+' "$skill_file" \
    || fail "public skill description is missing: $skill"
  grep -Fq 'read-only `/lookup`' "$skill_file" \
    || fail "public skill lacks provider-neutral optional context: $skill"
  grep -Fq 'Do not create a remote draft' "$skill_file" \
    || fail "public skill lacks authoring boundary: $skill"
  grep -Fq 'separate explicit publishing action' "$skill_file" \
    || fail "public skill lacks explicit publishing separation: $skill"
  grep -Fq "\$${skill}" "$metadata_file" \
    || fail "public skill default prompt does not invoke itself: $skill"

  if grep -Eq '^dependencies:' "$metadata_file"; then
    fail "social authoring skill requires a provider dependency: $skill"
  fi

  if grep -RFn 'TODO' "skills/public/$skill"; then
    fail "public skill contains unfinished placeholders: $skill"
  fi
done

canonical_terms=(
  'Agentic Constellation'
  'Agentic OS'
  'System'
  'Implementation'
  'System dependency'
  'Integration dependency'
  'Setup dependency'
  'Materialization'
  'Distribution Bundle'
)

for term in "${canonical_terms[@]}"; do
  grep -Fq "**${term}**" CONTEXT.md || fail "canonical term is missing: $term"
done

prohibited_path_fixtures=(
  docs/knowledge-system/domain.md
  modules/example/providers/config.yml
  nested/runtime/state.json
  docs/release-manifest.json
)

for fixture in "${prohibited_path_fixtures[@]}"; do
  path_is_prohibited "$fixture" \
    || fail "source policy does not reject nested fixture: $fixture"
done

path_is_prohibited docs/constellation.md \
  && fail 'source policy rejects the canonical constellation document'

while IFS= read -r -d '' path; do
  path_is_prohibited "$path" && fail "prohibited source path: $path"

  [[ ! -L "$path" ]] || fail "source must be self-contained, symlink found: $path"

  if [[ "$path" != scripts/check.sh ]]; then
    if grep -IEn '/Users/[^/]+/|/home/[^/]+/|[A-Za-z]:\\Users\\' -- "$path"; then
      fail "personal absolute path found: $path"
    else
      scan_status=$?
      [[ $scan_status -eq 1 ]] \
        || fail "personal-path scan failed for $path"
    fi
  fi
done < <(git ls-files -co --exclude-standard -z)

declare -A skill_paths=()
while IFS= read -r -d '' skill_file; do
  skill_file=${skill_file#./}
  case "$skill_file" in
    skills/public/*/SKILL.md|skills/internal/*/SKILL.md) ;;
    *) fail "skill definition is outside a canonical lane: $skill_file" ;;
  esac

  skill_name=$(sed -n 's/^name:[[:space:]]*//p' "$skill_file" | head -n 1)
  [[ -n "$skill_name" ]] || fail "skill name is missing: $skill_file"
  [[ "$(basename "$(dirname "$skill_file")")" == "$skill_name" ]] \
    || fail "skill directory and declared name differ: $skill_file"
  [[ -z "${skill_paths[$skill_name]:-}" ]] \
    || fail "duplicate skill definition: $skill_name"
  skill_paths[$skill_name]=$skill_file
done < <(find . -path ./.git -prune -o -type f -name SKILL.md -print0)

[[ "${skill_paths[domain-reconnaissance]:-}" == \
  skills/public/domain-reconnaissance/SKILL.md ]] \
  || fail 'domain-reconnaissance must be defined once in the public lane'
[[ "${skill_paths[setup-project]:-}" == skills/internal/setup-project/SKILL.md ]] \
  || fail 'setup-project must be defined once in the internal lane'

declare -A automation_paths=()
while IFS= read -r -d '' automation_file; do
  automation_file=${automation_file#./}
  case "$automation_file" in
    automations/internal/*/automation.toml) ;;
    *) fail "automation definition is outside the internal lane: $automation_file" ;;
  esac

  automation_id=$(sed -n 's/^id[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
    "$automation_file" | head -n 1)
  [[ -n "$automation_id" ]] || fail "automation id is missing: $automation_file"
  [[ -z "${automation_paths[$automation_id]:-}" ]] \
    || fail "duplicate automation definition: $automation_id"
  automation_paths[$automation_id]=$automation_file
done < <(find . -path ./.git -prune -o -type f -name automation.toml -print0)

[[ "${automation_paths[renovate-pr-ci-fixer]:-}" == \
  automations/internal/repo-pr-ci-repair-sweep/automation.toml ]] \
  || fail 'PR/CI repair sweep must be defined once in the internal lane'

if find skills/public -mindepth 2 -maxdepth 2 -type f ! -name SKILL.md -print -quit \
  | grep -q .; then
  fail 'public skill roots may contain only SKILL.md and self-contained subresources'
fi

grep -Fq 'bash scripts/check.sh' .github/workflows/check.yml \
  || fail 'clean-clone validation workflow does not run the source validator'
grep -Fq 'scripts/bump-version.sh' .github/workflows/release.yml \
  || fail 'release workflow does not use the independent version script'

printf 'check: ok\n'
