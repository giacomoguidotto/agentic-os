#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

fail() {
  printf 'check: %s\n' "$1" >&2
  exit 1
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
  scripts/bump-version.sh
  .github/workflows/check.yml
  .github/workflows/release.yml
)

for path in "${required_files[@]}"; do
  [[ -s "$path" ]] || fail "required source is missing or empty: $path"
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

while IFS= read -r -d '' path; do
  case "$path" in
    knowledge-system/*|mastery-system/*|career-ops/*)
      fail "System source copy is prohibited: $path"
      ;;
    providers/*|bindings/*|runtime/*|server/*|daemon/*)
      fail "provider or runtime source is prohibited: $path"
      ;;
    constellation.yml|constellation.yaml|constellation.json|constellation.toml|release-manifest.*)
      fail "synchronized constellation manifest is prohibited: $path"
      ;;
    local/*|*.pem|*.key|*.p12)
      fail "local state or credential material is prohibited: $path"
      ;;
  esac

  [[ ! -L "$path" ]] || fail "source must be self-contained, symlink found: $path"

  if [[ "$path" != scripts/check.sh ]] \
    && grep -IEn '/Users/[^/]+/|/home/[^/]+/|[A-Za-z]:\\Users\\' "$path"; then
    fail 'personal absolute path found'
  fi
done < <(git ls-files -co --exclude-standard -z)

grep -Fq 'bash scripts/check.sh' .github/workflows/check.yml \
  || fail 'clean-clone validation workflow does not run the source validator'
grep -Fq 'scripts/bump-version.sh' .github/workflows/release.yml \
  || fail 'release workflow does not use the independent version script'

printf 'check: ok\n'
