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
  skills/public/agentic-os/SKILL.md
  skills/public/agentic-os/agents/openai.yaml
  skills/public/agentic-os/resources/scout-knowledge-request.json
  skills/public/agentic-os/resources/scout-result.schema.json
  skills/public/agentic-os/resources/examples/scout-result.json
  skills/public/agentic-os/resources/pursue-knowledge-request.json
  skills/public/agentic-os/resources/pursue-result.schema.json
  skills/public/agentic-os/resources/examples/pursue-result.json
  scripts/bump-version.sh
  scripts/check-agentic-os-scout.py
  scripts/check-agentic-os-pursue.py
  .github/workflows/check.yml
  .github/workflows/release.yml
  skills/public/domain-reconnaissance/SKILL.md
  skills/internal/setup-project/SKILL.md
  skills/internal/setup-project/agents/openai.yaml
  skills/internal/setup-project/resources/repository-setup.md
  automations/internal/repo-pr-ci-repair-sweep/automation.toml
  automations/internal/repo-pr-ci-repair-sweep/prompt.md
  automations/internal/social-compose/automation.toml
  automations/internal/social-compose/knowledge-request.json
  automations/internal/social-compose/prompt.md
  automations/internal/portfolio-refresh/automation.toml
  automations/internal/portfolio-refresh/knowledge-request.json
  automations/internal/portfolio-refresh/prompt.md
  automations/internal/job-scout/automation.toml
  automations/internal/job-scout/prompt.md
  automations/internal/job-pursue/automation.toml
  automations/internal/job-pursue/prompt.md
)

for path in "${required_files[@]}"; do
  [[ -s "$path" ]] || fail "required source is missing or empty: $path"
done

python3 scripts/check-agentic-os-scout.py
python3 scripts/check-agentic-os-pursue.py

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
[[ "${automation_paths[social-draft-pulse]:-}" == \
  automations/internal/social-compose/automation.toml ]] \
  || fail 'Social Compose must be defined once in the internal lane'

SOCIAL_DIR=automations/internal/social-compose
python3 - "$SOCIAL_DIR/automation.toml" "$SOCIAL_DIR/knowledge-request.json" <<'PY'
import json
import sys
import tomllib

automation_path, request_path = sys.argv[1:]
with open(automation_path, "rb") as source:
    automation = tomllib.load(source)
with open(request_path, encoding="utf-8") as source:
    request = json.load(source)

expected_sources = {
    "social-publishing-source": {
        "required": True,
        "capabilities": {
            "publication-history",
            "post-analytics",
            "queue-timeline",
            "queue-schedule",
        },
    },
    "availability-calendar-source": {
        "required": False,
        "capabilities": {"upcoming-availability"},
    },
    "external-signal-source": {
        "required": False,
        "capabilities": {"current-public-signals"},
    },
}
sources = automation.get("sources", {})
if set(sources) != set(expected_sources):
    raise SystemExit("check: Social Compose source roles are invalid")
for role, expected in expected_sources.items():
    source = sources.get(role, {})
    actual = set(source.get("capabilities", []))
    if actual != expected["capabilities"]:
        raise SystemExit(f"check: Social Compose source contract is invalid: {role}")
    if source.get("required") is not expected["required"]:
        raise SystemExit(f"check: Social Compose source requirement is invalid: {role}")

sink = automation.get("sinks", {}).get("social-draft-queue", {})
if set(sink.get("capabilities", [])) != {"create-draft", "schedule-draft"}:
    raise SystemExit("check: Social Compose sink contract is invalid")
if sink.get("authority") != "approval-gated":
    raise SystemExit("check: Social Compose sink is not approval-gated")

validation = automation.get("validation", {})
if validation.get("profile") != "non-publishing":
    raise SystemExit("check: Social Compose validation profile is not non-publishing")
declared_source_capabilities = set().union(
    *(source["capabilities"] for source in expected_sources.values())
)
if set(validation.get("source_capabilities", [])) != declared_source_capabilities:
    raise SystemExit("check: Social Compose validation source capabilities are invalid")
if validation.get("sink_capabilities") != []:
    raise SystemExit("check: Social Compose validation grants sink capabilities")
required_prohibitions = {"create-draft", "schedule-draft", "publish"}
if not required_prohibitions.issubset(set(validation.get("prohibited_actions", []))):
    raise SystemExit("check: Social Compose validation can mutate social content")

if automation.get("knowledge_request_file") != "knowledge-request.json":
    raise SystemExit("check: Social Compose does not name its Knowledge Request")
if request.get("interface") != "knowledge-system-interface/v1":
    raise SystemExit("check: Social Compose Knowledge Request is not provider-blind")
if request.get("caller") != "agentic-os":
    raise SystemExit("check: Social Compose Knowledge Request caller is invalid")
if request.get("capability") != "agentic-os.social-compose":
    raise SystemExit("check: Social Compose Knowledge Request capability is invalid")

roles = request.get("roles", {})
if roles.get("required") != ["social-rules-of-engagement"]:
    raise SystemExit("check: Social Compose required Knowledge roles are not minimal")
allowed_roles = {
    "social-rules-of-engagement",
    "selected-projects",
    "public-safe-claim-source",
    "identity",
    "point-of-view",
    "published-social-context",
}
requested_roles = set(roles.get("required", [])) | set(roles.get("optional", []))
if requested_roles != allowed_roles:
    raise SystemExit("check: Social Compose Knowledge roles are invalid")

mandate = request.get("mandate", {})
if set(mandate.get("read_roles", [])) != allowed_roles:
    raise SystemExit("check: Social Compose read mandate exceeds its request")
if set(mandate.get("capture_roles", [])) != {
    "point-of-view",
    "published-social-context",
}:
    raise SystemExit("check: Social Compose capture mandate is invalid")
if not set(mandate.get("public_facing_roles", [])).issubset(allowed_roles):
    raise SystemExit("check: Social Compose public-facing mandate is invalid")
PY

if grep -IREn 'Notion|Typefully|Buffer|Hootsuite' "$SOCIAL_DIR"; then
  fail 'Social Compose contains a provider-specific dependency'
fi

grep -Fq 'This automation has no publishing authority.' "$SOCIAL_DIR/prompt.md" \
  || fail 'Social Compose does not separate publishing authority'
grep -Fqi 'do not call any sink capability' "$SOCIAL_DIR/prompt.md" \
  || fail 'Social Compose non-publishing validation can mutate its sink'

[[ "${automation_paths[portfolio-surface-sweep]:-}" == \
  automations/internal/portfolio-refresh/automation.toml ]] \
  || fail 'Portfolio Refresh must be defined once in the internal lane'

PORTFOLIO_DIR=automations/internal/portfolio-refresh
python3 - "$PORTFOLIO_DIR/automation.toml" \
  "$PORTFOLIO_DIR/knowledge-request.json" <<'PY'
import json
import sys
import tomllib

automation_path, request_path = sys.argv[1:]
with open(automation_path, "rb") as source:
    automation = tomllib.load(source)
with open(request_path, encoding="utf-8") as source:
    request = json.load(source)

source = automation.get("sources", {}).get("portfolio-source", {})
if source.get("required") is not True:
    raise SystemExit("check: Portfolio Refresh source is not required")
if set(source.get("capabilities", [])) != {
    "repository-instructions",
    "current-state",
}:
    raise SystemExit("check: Portfolio Refresh source contract is invalid")

sink = automation.get("sinks", {}).get("portfolio", {})
if set(sink.get("capabilities", [])) != {
    "create-branch",
    "edit-files",
    "run-validation",
    "open-draft-pr",
}:
    raise SystemExit("check: Portfolio Refresh sink contract is invalid")
if sink.get("authority") != "approval-gated":
    raise SystemExit("check: Portfolio Refresh sink is not approval-gated")

validation = automation.get("validation", {})
if validation.get("profile") != "proposal-only":
    raise SystemExit("check: Portfolio Refresh validation is not proposal-only")
if set(validation.get("source_capabilities", [])) != {
    "repository-instructions",
    "current-state",
}:
    raise SystemExit("check: Portfolio Refresh validation source contract is invalid")
if validation.get("sink_capabilities") != []:
    raise SystemExit("check: Portfolio Refresh validation grants sink capabilities")
required_prohibitions = {
    "create-branch",
    "edit-files",
    "open-draft-pr",
    "merge",
    "deploy",
    "publish",
    "knowledge-capture",
}
if not required_prohibitions.issubset(
    set(validation.get("prohibited_actions", []))
):
    raise SystemExit("check: Portfolio Refresh validation permits mutation")

if automation.get("knowledge_request_file") != "knowledge-request.json":
    raise SystemExit("check: Portfolio Refresh does not name its Knowledge Request")
if request.get("interface") != "knowledge-system-interface/v1":
    raise SystemExit("check: Portfolio Refresh Knowledge Request is not versioned")
if request.get("caller") != "agentic-os":
    raise SystemExit("check: Portfolio Refresh Knowledge Request caller is invalid")
if request.get("capability") != "agentic-os.portfolio-refresh":
    raise SystemExit("check: Portfolio Refresh Knowledge Request capability is invalid")

roles = request.get("roles", {})
if roles.get("required") != ["portfolio-change-rules"]:
    raise SystemExit("check: Portfolio Refresh required Knowledge roles are invalid")
allowed_roles = {
    "public-safe-claim-source",
    "network",
    "selected-projects",
    "portfolio-change-rules",
    "identity",
}
requested_roles = set(roles.get("required", [])) | set(
    roles.get("optional", [])
)
if requested_roles != allowed_roles:
    raise SystemExit("check: Portfolio Refresh Knowledge roles are invalid")

mandate = request.get("mandate", {})
if set(mandate.get("read_roles", [])) != allowed_roles:
    raise SystemExit("check: Portfolio Refresh read mandate exceeds its request")
if mandate.get("capture_roles") != []:
    raise SystemExit("check: Portfolio Refresh capture mandate is not empty")
public_roles = {
    "public-safe-claim-source",
    "network",
    "selected-projects",
    "identity",
}
if set(mandate.get("public_facing_roles", [])) != public_roles:
    raise SystemExit("check: Portfolio Refresh public-facing roles are invalid")
PY

if grep -IREn 'Notion|Vercel|Netlify' "$PORTFOLIO_DIR"; then
  fail 'Portfolio Refresh contains a provider-specific dependency'
fi

grep -Fq 'This automation has no Knowledge capture authority.' \
  "$PORTFOLIO_DIR/prompt.md" \
  || fail 'Portfolio Refresh does not declare its empty capture mandate'
grep -Fqi 'do not call any sink capability' "$PORTFOLIO_DIR/prompt.md" \
  || fail 'Portfolio Refresh proposal-only validation can mutate its sink'
grep -Fqi 'Never merge, deploy, publish' "$PORTFOLIO_DIR/prompt.md" \
  || fail 'Portfolio Refresh lacks terminal authority boundaries'
grep -Fqi 'mutate Knowledge' "$PORTFOLIO_DIR/prompt.md" \
  || fail 'Portfolio Refresh can mutate Knowledge'

[[ "${automation_paths[career-ops-scan-and-evaluate]:-}" == \
  automations/internal/job-scout/automation.toml ]] \
  || fail 'Job Scout must be defined once in the internal lane'

JOB_SCOUT_DIR=automations/internal/job-scout
python3 - "$JOB_SCOUT_DIR/automation.toml" <<'PY'
import sys
import tomllib

with open(sys.argv[1], "rb") as source:
    automation = tomllib.load(source)

invocation = automation.get("invocation", {})
if invocation.get("capability") != "agentic-os.scout":
    raise SystemExit("check: Job Scout does not invoke agentic-os.scout")
if invocation.get("arguments") != ["--target", "30"]:
    raise SystemExit("check: Job Scout target is invalid")

if automation.get("prompt_file") != "prompt.md":
    raise SystemExit("check: Job Scout does not name its bundled prompt")

validation = automation.get("validation", {})
if validation.get("profile") != "non-publishing-no-write":
    raise SystemExit("check: Job Scout validation is not non-publishing and no-write")
if validation.get("invoke_capability") is not False:
    raise SystemExit("check: Job Scout validation invokes a mutating capability")
if validation.get("source_capabilities") != []:
    raise SystemExit("check: Job Scout validation grants source capabilities")
if validation.get("sink_capabilities") != []:
    raise SystemExit("check: Job Scout validation grants sink capabilities")
required_prohibitions = {
    "application",
    "outreach",
    "message",
    "knowledge-write",
    "career-write",
    "publish",
}
if not required_prohibitions.issubset(
    set(validation.get("prohibited_actions", []))
):
    raise SystemExit("check: Job Scout validation permits external or System writes")
PY

grep -Fq 'Invoke only the installed `agentic-os.scout` capability' \
  "$JOB_SCOUT_DIR/prompt.md" \
  || fail 'Job Scout does not route through agentic-os.scout'
grep -Fqi 'do not invoke `agentic-os.scout` or any System capability' \
  "$JOB_SCOUT_DIR/prompt.md" \
  || fail 'Job Scout validation can invoke a mutating capability'
grep -Fqi 'submit an application' "$JOB_SCOUT_DIR/prompt.md" \
  || fail 'Job Scout validation can submit an application'
grep -Fqi 'perform outreach' "$JOB_SCOUT_DIR/prompt.md" \
  || fail 'Job Scout validation can perform outreach'
grep -Fqi 'send a message' "$JOB_SCOUT_DIR/prompt.md" \
  || fail 'Job Scout validation can send a message'
grep -Fqi 'write to Knowledge' "$JOB_SCOUT_DIR/prompt.md" \
  || fail 'Job Scout validation can write to Knowledge'

if grep -IREn \
  'node main\.mjs|career\.opportunity\.discover|career\.profile\.|knowledge-system-interface|/lookup|/capture' \
  "$JOB_SCOUT_DIR"; then
  fail 'Job Scout duplicates Career or Knowledge semantics'
fi

[[ "${automation_paths[job-hunt-advancement-pulse]:-}" == \
  automations/internal/job-pursue/automation.toml ]] \
  || fail 'Job Pursue must be defined once in the internal lane'

JOB_PURSUE_DIR=automations/internal/job-pursue
python3 - "$JOB_PURSUE_DIR/automation.toml" <<'PY'
import sys
import tomllib

with open(sys.argv[1], "rb") as source:
    automation = tomllib.load(source)

invocation = automation.get("invocation", {})
if invocation.get("capability") != "agentic-os.pursue":
    raise SystemExit("check: Job Pursue does not invoke agentic-os.pursue")
if invocation.get("arguments") != []:
    raise SystemExit("check: Job Pursue declares unsupported arguments")

if automation.get("prompt_file") != "prompt.md":
    raise SystemExit("check: Job Pursue does not name its bundled prompt")

validation = automation.get("validation", {})
if validation.get("profile") != "non-publishing-no-write":
    raise SystemExit("check: Job Pursue validation is not non-publishing and no-write")
if validation.get("invoke_capability") is not False:
    raise SystemExit("check: Job Pursue validation invokes a mutating capability")
if validation.get("source_capabilities") != []:
    raise SystemExit("check: Job Pursue validation grants source capabilities")
if validation.get("sink_capabilities") != []:
    raise SystemExit("check: Job Pursue validation grants sink capabilities")
required_prohibitions = {
    "application",
    "outreach",
    "message",
    "contact",
    "factual-event-write",
    "knowledge-write",
    "career-write",
    "publish",
}
if not required_prohibitions.issubset(
    set(validation.get("prohibited_actions", []))
):
    raise SystemExit("check: Job Pursue validation permits external or System writes")
PY

grep -Fq 'Invoke only the installed `agentic-os.pursue` capability' \
  "$JOB_PURSUE_DIR/prompt.md" \
  || fail 'Job Pursue does not route through agentic-os.pursue'
grep -Fqi 'do not invoke `agentic-os.pursue` or any System capability' \
  "$JOB_PURSUE_DIR/prompt.md" \
  || fail 'Job Pursue validation can invoke a mutating capability'
grep -Fqi 'required_approvals' "$JOB_PURSUE_DIR/prompt.md" \
  || fail 'Job Pursue drops required human approvals'
grep -Fqi 'evidence_sufficiency' "$JOB_PURSUE_DIR/prompt.md" \
  || fail 'Job Pursue drops native evidence gates'
grep -Fqi 'submit an application' "$JOB_PURSUE_DIR/prompt.md" \
  || fail 'Job Pursue validation can submit an application'
grep -Fqi 'contact a person' "$JOB_PURSUE_DIR/prompt.md" \
  || fail 'Job Pursue validation can contact a person'
grep -Fqi 'factual real-world event' "$JOB_PURSUE_DIR/prompt.md" \
  || fail 'Job Pursue validation can assert a real-world event'
grep -Fqi 'write to Knowledge' "$JOB_PURSUE_DIR/prompt.md" \
  || fail 'Job Pursue validation can write to Knowledge'

if grep -IREn \
  'node main\.mjs|career\.opportunity\.|career\.profile\.|knowledge-system-interface|/lookup|/capture' \
  "$JOB_PURSUE_DIR"; then
  fail 'Job Pursue duplicates Career or Knowledge semantics'
fi

if find skills/public -mindepth 2 -maxdepth 2 -type f ! -name SKILL.md -print -quit \
  | grep -q .; then
  fail 'public skill roots may contain only SKILL.md and self-contained subresources'
fi

grep -Fq 'bash scripts/check.sh' .github/workflows/check.yml \
  || fail 'clean-clone validation workflow does not run the source validator'
grep -Fq 'scripts/bump-version.sh' .github/workflows/release.yml \
  || fail 'release workflow does not use the independent version script'

printf 'check: ok\n'
