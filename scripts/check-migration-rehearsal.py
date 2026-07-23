#!/usr/bin/env python3
"""Rehearse prepare, pause, migrate, validate, and resume without publishing."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPOSITORY_ROOT / "scripts" / "fixtures"
RELEASE_MANIFEST = FIXTURES / "migration-releases.json"
SYSTEM_COMMAND = FIXTURES / "migration-system-command.py"
BUNDLE_COMMAND = FIXTURES / "migration-bundle-command.py"
SETUP_COMMAND = (
    REPOSITORY_ROOT
    / "skills"
    / "public"
    / "setup-agentic-os"
    / "scripts"
    / "setup-agentic-os.py"
)
AUTOMATION_COMMAND = SETUP_COMMAND.with_name("reconcile-automation-sources.py")
SYSTEM_KEYS = ("knowledge-system", "mastery-system", "career-ops")
SYSTEM_ORDER = ("career", "mastery", "knowledge")
SYSTEM_KEY = {
    "knowledge": "knowledge-system",
    "mastery": "mastery-system",
    "career": "career-ops",
}
REPOSITORY = {
    "knowledge": "giacomoguidotto/knowledge-system",
    "mastery": "giacomoguidotto/mastery-system",
    "career": "giacomoguidotto/career-system",
}
BRANCH = {"knowledge": "main", "mastery": "main", "career": "fork/main"}
REQUIRED_PATHS = {
    "knowledge": (
        "skills/public/setup-knowledge-system/SKILL.md",
        "skills/public/setup-knowledge-system/resources/knowledge-system-interface/v1",
    ),
    "mastery": (
        "skills/public/setup-mastery-system/SKILL.md",
        "skills/public/setup-mastery-system/resources/setup.mjs",
    ),
    "career": (
        "main.mjs",
        "skills/public/setup-career-system/SKILL.md",
        "skills/public/setup-career-system/scripts/setup-career-system.mjs",
    ),
}


def run(
    *arguments: str,
    cwd: Path | None = None,
    input_document: dict[str, Any] | None = None,
    environment: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        input=json.dumps(input_document) if input_document is not None else None,
        env=environment,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def json_run(
    *arguments: str,
    cwd: Path | None = None,
    input_document: dict[str, Any] | None = None,
    environment: dict[str, str] | None = None,
    check: bool = True,
) -> dict[str, Any]:
    completed = run(
        *arguments,
        cwd=cwd,
        input_document=input_document,
        environment=environment,
        check=check,
    )
    return json.loads(completed.stdout)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def skill(path: Path, name: str, body: str = "") -> None:
    write(
        path / "SKILL.md",
        f"---\nname: {name}\ndescription: Immutable migration fixture\n---\n\n"
        f"# {name}\n\n{body or 'Self-contained fixture release module.'}\n",
    )


def tree_manifest(root: Path) -> list[tuple[str, str]]:
    if not root.exists():
        return []
    return [
        (
            str(path.relative_to(root)),
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    ]


def tree_digest(root: Path) -> str:
    return hashlib.sha256(json.dumps(tree_manifest(root)).encode()).hexdigest()


def fixture_release_root(releases: Path, repository: str) -> Path:
    return releases / repository.replace("/", "__")


def create_release_fixtures(releases: Path) -> None:
    exports = {
        "giacomoguidotto/agentic-os": (
            "agentic-os",
            "post",
            "setup-agentic-os",
        ),
        "giacomoguidotto/knowledge-system": (
            "capture",
            "lookup",
            "setup-knowledge-system",
        ),
        "giacomoguidotto/mastery-system": ("setup-mastery-system",),
        "giacomoguidotto/career-system": (
            "setup-career-system",
            "career-operational-private",
        ),
    }
    for repository, names in exports.items():
        root = fixture_release_root(releases, repository)
        for name in names:
            skill(root / "skills" / "public" / name, name)
    skill(
        fixture_release_root(releases, "giacomoguidotto/agentic-os")
        / "skills"
        / "internal"
        / "setup-project",
        "setup-project",
    )
    skill(
        fixture_release_root(releases, "giacomoguidotto/knowledge-system")
        / "skills"
        / "internal"
        / "get-knowledge",
        "get-knowledge",
    )


def node_wrapper(system: str, command: str) -> str:
    return f"""#!/usr/bin/env node
import {{ spawnSync }} from "node:child_process";
import {{ readFileSync }} from "node:fs";
import process from "node:process";
const command = {json.dumps(str(SYSTEM_COMMAND))};
const args = process.argv.slice(2);
let childArgs;
if ({json.dumps(command)} === "setup") {{
  const mode = args[0] ?? "reconcile";
  const rootIndex = args.indexOf("--root");
  const harnessIndex = args.indexOf("--harness");
  childArgs = [command, "setup", {json.dumps(system)}, mode,
    "--root", args[rootIndex + 1], "--harness", args[harnessIndex + 1]];
}} else {{
  const capability = args[0];
  childArgs = [command, "gateway", {json.dumps(system)}, capability,
    "--root", process.cwd()];
}}
const child = spawnSync("python3", childArgs, {{
  cwd: process.cwd(), input: readFileSync(0, "utf8"), encoding: "utf8"
}});
process.stdout.write(child.stdout ?? "");
process.stderr.write(child.stderr ?? "");
process.exitCode = child.status ?? 1;
"""


def initialize_repository(root: Path, system: str, harness: Path) -> None:
    for required in REQUIRED_PATHS[system]:
        path = root / required
        if Path(required).suffix:
            write(path, "fixture\n")
        else:
            write(path / "README.md", "immutable interface fixture\n")
    write(root / ".gitignore", "local/\nstate/\nconfig/career-profile.json\nmodes/_profile.md\n")
    if system == "knowledge":
        desired = root / "release" / "knowledge-system-interface" / "v1"
        write(desired / "README.md", "provider-blind interface fixture\n")
        write(desired / "validate-snapshot-token.py", "# fixture executable\n")
        write(
            root / "skills" / "public" / "setup-knowledge-system" / "SKILL.md",
            "---\nname: setup-knowledge-system\ndescription: Fixture\n---\n",
        )
        write(root / "local" / "bindings.yml", "provider: fixture\nconnector: isolated\nunknown-key: preserve\n")
        write(root / "state" / "knowledge-revision", "revision-1\n")
    elif system == "mastery":
        setup_path = root / "skills" / "public" / "setup-mastery-system" / "resources" / "setup.mjs"
        write(setup_path, node_wrapper(system, "setup"))
        write(root / "main.mjs", node_wrapper(system, "gateway"))
        write(root / "state" / "cycles.json", json.dumps({"cycles": [], "history": ["pre-migration-assessment"]}) + "\n")
    else:
        setup_path = root / "skills" / "public" / "setup-career-system" / "scripts" / "setup-career-system.mjs"
        write(setup_path, node_wrapper(system, "setup"))
        write(root / "main.mjs", node_wrapper(system, "gateway"))
        write(root / "modes" / "_profile.template.md", "# Local profile\n")
        write(root / "cv.md", "preserve career source\n")
        write(root / "config" / "profile.yml", "target: fixture\n")
        write(root / "portals.yml", "providers: []\n")
        write(root / "data" / "applications.md", "application history must not change\n")
        write(root / "data" / "approach-attempts.md", "message history must not change\n")
        write(root / "reports" / "001-existing.md", "operational record must not change\n")
    run("git", "init", "-b", BRANCH[system], cwd=root)
    run("git", "config", "user.name", "Migration Rehearsal", cwd=root)
    run("git", "config", "user.email", "rehearsal@example.invalid", cwd=root)
    run("git", "add", ".", cwd=root)
    run("git", "commit", "-m", "test: immutable System fixture", cwd=root)
    run(
        "git",
        "remote",
        "add",
        "origin",
        f"https://github.com/{REPOSITORY[system]}.git",
        cwd=root,
    )


def create_fake_git(bin_root: Path) -> dict[str, str]:
    real_git = shutil.which("git")
    if real_git is None:
        raise AssertionError("git is required")
    wrapper = bin_root / "git"
    write(
        wrapper,
        "#!/usr/bin/env python3\n"
        "import os, subprocess, sys\n"
        "if len(sys.argv) >= 3 and sys.argv[1] == 'ls-remote':\n"
        "    head = subprocess.check_output([os.environ['REAL_GIT'], 'rev-parse', 'HEAD'], text=True).strip()\n"
        "    print(f'{head}\\t{sys.argv[-1]}')\n"
        "    raise SystemExit(0)\n"
        "os.execv(os.environ['REAL_GIT'], [os.environ['REAL_GIT'], *sys.argv[1:]])\n",
    )
    wrapper.chmod(0o755)
    environment = os.environ.copy()
    environment["REAL_GIT"] = real_git
    environment["PATH"] = f"{bin_root}{os.pathsep}{environment['PATH']}"
    return environment


def system_setup(system: str, mode: str, root: Path, harness: Path) -> dict[str, Any]:
    if system == "knowledge":
        return json_run(
            "python3",
            str(SYSTEM_COMMAND),
            "setup",
            system,
            mode,
            "--root",
            str(root),
            "--harness",
            str(harness),
        )
    setup_path = (
        root / "skills" / "public" / "setup-mastery-system" / "resources" / "setup.mjs"
        if system == "mastery"
        else root / "skills" / "public" / "setup-career-system" / "scripts" / "setup-career-system.mjs"
    )
    return json_run(
        "node",
        str(setup_path),
        mode,
        "--root",
        str(root),
        "--harness",
        str(harness),
        cwd=root,
    )


def gateway(system: str, capability: str, root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if system == "knowledge":
        return json_run(
            "python3",
            str(SYSTEM_COMMAND),
            "gateway",
            system,
            capability,
            "--root",
            str(root),
            input_document=payload,
        )
    return json_run(
        "node",
        "main.mjs",
        capability,
        "--input",
        "-",
        cwd=root,
        input_document=payload,
    )


def read_automation_map() -> list[dict[str, Any]]:
    path = (
        REPOSITORY_ROOT
        / "skills"
        / "public"
        / "setup-agentic-os"
        / "resources"
        / "automation-migration.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))["automations"]


def initialize_harness(harness: Path) -> None:
    installed = harness / "skills"
    for name in ("agentic-os", "post", "lookup", "setup-career-system"):
        skill(installed / name, name, "superseded first-party materialization")
    skill(installed / "third-party-tool", "third-party-tool", "must remain untouched")
    skill(installed / "local-helper", "local-helper", "unrelated local skill")
    write(harness / "first-party.json", json.dumps(["agentic-os", "post", "lookup", "setup-career-system"]) + "\n")
    live = harness / "automations"
    for index, automation in enumerate(read_automation_map(), start=1):
        root = live / automation["stable_identity"]
        write(root / "definition" / "prompt.md", "retired definition\n")
        metadata = {
            "id": automation["stable_identity"],
            "schedule": f"{index} 7 * * *",
            "timezone": "Europe/Rome",
            "enabled": True,
            "bindings": {"provider": f"fixture-{index}"},
            "runtime_handle": f"runtime-{index}",
            "history": [f"run-{index}-a", f"run-{index}-b"],
            "last_completed_at": f"2026-07-{index:02d}T07:00:00+02:00",
        }
        write(root / "metadata.json", json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    write(harness / "operational-record.log", "must remain untouched\n")


def pause_or_resume(harness: Path, enabled: bool) -> None:
    for automation in read_automation_map():
        path = harness / "automations" / automation["stable_identity"] / "metadata.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["enabled"] = enabled
        payload = json.dumps(document, indent=2, sort_keys=True) + "\n"
        if path.read_text(encoding="utf-8") != payload:
            path.write_text(payload, encoding="utf-8")


def publish_fixture_bundle(releases: Path, bundle: Path) -> str:
    result = json_run(
        "python3",
        str(BUNDLE_COMMAND),
        "--manifest",
        str(RELEASE_MANIFEST),
        "--releases",
        str(releases),
        "--output",
        str(bundle),
    )
    if result["status"] == "failed":
        raise AssertionError(result)
    return result["status"]


def install_bundle(harness: Path, bundle: Path, releases: Path) -> None:
    installed = harness / "skills"
    first_party_path = harness / "first-party.json"
    old_first_party = set(json.loads(first_party_path.read_text(encoding="utf-8")))
    desired = {path.name for path in (bundle / "skills").iterdir() if path.is_dir()}
    for name in sorted(old_first_party - desired):
        shutil.rmtree(installed / name)
    for name in sorted(desired):
        source = bundle / "skills" / name
        target = installed / name
        if tree_manifest(source) == tree_manifest(target):
            continue
        candidate = installed / f".{name}.candidate"
        if candidate.exists():
            shutil.rmtree(candidate)
        shutil.copytree(source, candidate)
        if target.exists():
            shutil.rmtree(target)
        candidate.replace(target)
    internal_source = (
        fixture_release_root(releases, "giacomoguidotto/knowledge-system")
        / "skills"
        / "internal"
        / "get-knowledge"
    )
    internal_target = installed / "get-knowledge"
    if tree_manifest(internal_source) != tree_manifest(internal_target):
        if internal_target.exists():
            shutil.rmtree(internal_target)
        shutil.copytree(internal_source, internal_target)
    first_party_path.write_text(json.dumps(sorted(desired | {"get-knowledge"})) + "\n", encoding="utf-8")


def reconcile_automations(harness: Path) -> dict[str, Any]:
    lane = harness / "automation-sources"
    result = json_run(
        "python3",
        str(AUTOMATION_COMMAND),
        "reconcile",
        "--target-root",
        str(lane),
    )
    for automation in read_automation_map():
        source = lane / automation["name"]
        target = harness / "automations" / automation["stable_identity"] / "definition"
        if tree_manifest(source) == tree_manifest(target):
            continue
        candidate = target.with_name(".definition.candidate")
        if candidate.exists():
            shutil.rmtree(candidate)
        shutil.copytree(source, candidate)
        if target.exists():
            shutil.rmtree(target)
        candidate.replace(target)
    return result


def integration_blockers(repository_result: dict[str, Any]) -> dict[str, str]:
    statuses = {branch["key"]: branch["status"] for branch in repository_result["branches"]}
    results = {
        automation["stable_identity"]: (
            "converged"
            if all(statuses[dependency] == "converged" for dependency in automation["dependencies"])
            else "blocked"
        )
        for automation in read_automation_map()
    }
    results["agentic-os.upskill"] = (
        "converged"
        if all(
            statuses[key] == "converged"
            for key in ("knowledge-system", "mastery-system", "career-ops")
        )
        else "blocked"
    )
    return results


def full_state(harness: Path, roots: dict[str, Path], bundle: Path) -> dict[str, Any]:
    return {
        "repositories": {
            key: {
                "head": run("git", "rev-parse", "HEAD", cwd=root).stdout.strip(),
                "tracked": run("git", "status", "--short", cwd=root).stdout,
                "content": tree_digest(root),
            }
            for key, root in roots.items()
        },
        "installed": tree_manifest(harness / "skills"),
        "interface": tree_manifest(harness / "skills" / "knowledge-system-interface"),
        "automations": tree_manifest(harness / "automations"),
        "automation_sources": tree_manifest(harness / "automation-sources"),
        "bundle": tree_manifest(bundle),
        "operational_record": (harness / "operational-record.log").read_bytes().hex(),
    }


def assert_preserved(before: dict[str, bytes], after: dict[str, bytes], label: str) -> None:
    if before != after:
        raise AssertionError(f"{label} was not preserved")


def main() -> None:
    manifest = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
    if manifest["publisher"]["contract"] != "distribution-provenance/v1":
        raise AssertionError("publisher fixture does not name the current contract")
    with tempfile.TemporaryDirectory(prefix="agentic-os-migration-rehearsal-") as raw:
        temporary = Path(raw)
        releases = temporary / "immutable-releases"
        harness = temporary / "harness"
        bundle = temporary / "distribution-bundle"
        roots = {
            system: temporary / "systems" / SYSTEM_KEY[system]
            for system in SYSTEM_ORDER
        }
        create_release_fixtures(releases)
        initialize_harness(harness)
        for system, root in roots.items():
            root.mkdir(parents=True)
            initialize_repository(root, system, harness)
        registry = temporary / "installation.yml"
        write(
            registry,
            "repositories:\n"
            + "".join(f"  {key}: {roots[system]}\n" for system, key in (
                ("knowledge", "knowledge-system"),
                ("mastery", "mastery-system"),
                ("career", "career-ops"),
            )),
        )
        environment = create_fake_git(temporary / "bin")

        bindings_before = (roots["knowledge"] / "local" / "bindings.yml").read_bytes()
        career_paths = (
            roots["career"] / "data" / "applications.md",
            roots["career"] / "data" / "approach-attempts.md",
            roots["career"] / "reports" / "001-existing.md",
        )
        career_before = {str(path): path.read_bytes() for path in career_paths}
        third_party_before = {
            name: tree_manifest(harness / "skills" / name)
            for name in ("third-party-tool", "local-helper")
        }
        automation_metadata_before = {
            automation["stable_identity"]: (
                harness / "automations" / automation["stable_identity"] / "metadata.json"
            ).read_bytes()
            for automation in read_automation_map()
        }

        repository_check = json_run(
            "python3",
            str(SETUP_COMMAND),
            "check",
            "--registry",
            str(registry),
            environment=environment,
        )
        if repository_check["status"] != "converged" or repository_check["writes"]:
            raise AssertionError(f"prepare repository check failed: {repository_check}")

        setup_results = {}
        for system in SYSTEM_ORDER:
            checked = system_setup(system, "check", roots[system], harness)
            reconciled = system_setup(system, "reconcile", roots[system], harness)
            final = system_setup(system, "check", roots[system], harness)
            if final["status"] != "converged":
                raise AssertionError(f"{system} did not become independently ready: {final}")
            setup_results[system] = (checked, reconciled, final)

        dirty = roots["mastery"] / "unsafe-user-work"
        write(dirty, "preserve exactly\n")
        dirty_head = run("git", "rev-parse", "HEAD", cwd=roots["mastery"]).stdout
        blocked = json_run(
            "python3",
            str(SETUP_COMMAND),
            "reconcile",
            "--registry",
            str(registry),
            environment=environment,
        )
        branches = {branch["key"]: branch for branch in blocked["branches"]}
        if (
            blocked["status"] != "blocked"
            or branches["mastery-system"]["reason"] != "dirty-worktree"
            or branches["knowledge-system"]["status"] != "converged"
            or branches["career-ops"]["status"] != "converged"
            or dirty.read_text(encoding="utf-8") != "preserve exactly\n"
            or run("git", "rev-parse", "HEAD", cwd=roots["mastery"]).stdout != dirty_head
        ):
            raise AssertionError("unsafe Git blocker was not preserved and scoped")
        scoped = integration_blockers(blocked)
        if scoped["renovate-pr-ci-fixer"] != "converged" or any(
            scoped[name] != "converged"
            for name in (
                "social-draft-pulse",
                "portfolio-surface-sweep",
                "career-ops-scan-and-evaluate",
                "job-hunt-advancement-pulse",
            )
        ):
            raise AssertionError("independent blocker stopped healthy automation branches")
        if scoped["agentic-os.upskill"] != "blocked":
            raise AssertionError("Mastery blocker did not stop its dependent integration")
        dirty.unlink()

        pause_or_resume(harness, False)
        if any(
            json.loads(
                (
                    harness / "automations" / automation["stable_identity"] / "metadata.json"
                ).read_text(encoding="utf-8")
            )["enabled"]
            for automation in read_automation_map()
        ):
            raise AssertionError("pause did not disable every affected automation")

        first_bundle = publish_fixture_bundle(releases, bundle)
        if first_bundle != "changed":
            raise AssertionError("first Distribution Bundle reconcile applied no delta")
        run("git", "init", "-b", "main", cwd=bundle)
        run("git", "config", "user.name", "Fixture Publisher", cwd=bundle)
        run("git", "config", "user.email", "publisher@example.invalid", cwd=bundle)
        run("git", "add", "skills", "provenance.lock.json", cwd=bundle)
        run("git", "commit", "-m", "chore: publish fixture Distribution Bundle", cwd=bundle)
        bundle_commit = run("git", "rev-parse", "HEAD", cwd=bundle).stdout.strip()
        install_bundle(harness, bundle, releases)
        first_automations = reconcile_automations(harness)
        if not first_automations["writes"]:
            raise AssertionError("first automation reconcile applied no delta")

        snapshot = gateway(
            "knowledge",
            "knowledge.snapshot/v1",
            roots["knowledge"],
            {
                "roles": ["identity", "selected-projects"],
                "capability": "agentic-os.upskill",
            },
        )
        if (
            snapshot["status"] != "ready"
            or not snapshot["snapshot_token"]
            or any(result["state"] != "value" for result in snapshot["results"])
            or any(not result["evidence"] or not result["provenance"] for result in snapshot["results"])
        ):
            raise AssertionError("Knowledge snapshot contract was not exercised")
        scoped_knowledge_blocker = gateway(
            "knowledge",
            "knowledge.snapshot/v1",
            roots["knowledge"],
            {
                "roles": ["unknown-role"],
                "capability": "agentic-os.social-compose",
            },
        )
        if (
            scoped_knowledge_blocker["status"] != "blocked"
            or scoped_knowledge_blocker["capability"] != "agentic-os.social-compose"
            or gateway(
                "knowledge",
                "knowledge.snapshot/v1",
                roots["knowledge"],
                {"roles": ["identity"], "capability": "agentic-os.upskill"},
            )["status"]
            != "ready"
        ):
            raise AssertionError("Knowledge blocker escaped its dependent capability")
        unchanged = gateway(
            "knowledge",
            "knowledge.snapshot-token.validate/v1",
            roots["knowledge"],
            {
                "roles": ["identity", "selected-projects"],
                "capability": "agentic-os.upskill",
                "snapshot_token": snapshot["snapshot_token"],
            },
        )
        if unchanged["status"] != "unchanged":
            raise AssertionError("fresh Knowledge token was not valid")
        (roots["knowledge"] / "state" / "knowledge-revision").write_text("revision-2\n", encoding="utf-8")
        changed = gateway(
            "knowledge",
            "knowledge.snapshot-token.validate/v1",
            roots["knowledge"],
            {
                "roles": ["identity", "selected-projects"],
                "capability": "agentic-os.upskill",
                "snapshot_token": snapshot["snapshot_token"],
            },
        )
        blocked_capture = gateway(
            "knowledge",
            "knowledge.capture/v1",
            roots["knowledge"],
            {"meaning": "must never be written"},
        )
        if changed["status"] != "changed" or blocked_capture["operations"]:
            raise AssertionError("Knowledge drift or no-capture boundary failed")

        career_payload = {
            "revision": "career-profile-revision-1",
            "profile": {"target": "fixture-role", "location": "remote"},
        }
        career_first = gateway(
            "career",
            "career.profile.reconcile/v1",
            roots["career"],
            career_payload,
        )
        career_second = gateway(
            "career",
            "career.profile.reconcile/v1",
            roots["career"],
            career_payload,
        )
        if not career_first["writes"] or career_second["writes"]:
            raise AssertionError("Career gateway did not converge idempotently")

        mappings = {
            "mappings": [
                {"mapping_key": "mapping:foundation", "dependencies": []},
                {"mapping_key": "mapping:delivery", "dependencies": ["mapping:foundation"]},
            ]
        }
        mastery_first = gateway(
            "mastery",
            "mastery.cycles.reconcile/v1",
            roots["mastery"],
            mappings,
        )
        mastery_second = gateway(
            "mastery",
            "mastery.cycles.reconcile/v1",
            roots["mastery"],
            mappings,
        )
        if (
            not mastery_first["writes"]
            or mastery_second["writes"]
            or [cycle["mapping_key"] for cycle in mastery_second["cycles"]]
            != ["mapping:delivery", "mapping:foundation"]
            or mastery_second["history"] != ["pre-migration-assessment"]
        ):
            raise AssertionError(
                f"Mastery mapping lifecycle was not stable: "
                f"first={mastery_first} second={mastery_second}"
            )

        provenance_text = (bundle / "provenance.lock.json").read_text(encoding="utf-8")
        provenance = json.loads(provenance_text)
        bundled_names = sorted(path.name for path in (bundle / "skills").iterdir())
        if (
            provenance["schema"] != "distribution-provenance/v1"
            or any(
                set(source)
                != {
                    "repository",
                    "release_id",
                    "tag",
                    "commit",
                    "archive_sha256",
                    "exports",
                }
                for source in provenance["sources"]
            )
            or any(token in provenance_text.lower() for token in ("timestamp", "generated_at", "created_at"))
            or "career-operational-private" in bundled_names
            or "third-party-tool" in bundled_names
        ):
            raise AssertionError("Distribution allowlist or deterministic provenance failed")

        pause_or_resume(harness, True)
        for identity, before in automation_metadata_before.items():
            after = json.loads((harness / "automations" / identity / "metadata.json").read_text(encoding="utf-8"))
            expected = json.loads(before)
            if after != expected:
                raise AssertionError(f"automation installation-local state changed: {identity}")

        assert_preserved(
            {str(roots["knowledge"] / "local" / "bindings.yml"): bindings_before},
            {str(roots["knowledge"] / "local" / "bindings.yml"): (roots["knowledge"] / "local" / "bindings.yml").read_bytes()},
            "Knowledge bindings",
        )
        assert_preserved(
            career_before,
            {str(path): path.read_bytes() for path in career_paths},
            "Career operational records",
        )
        if third_party_before != {
            name: tree_manifest(harness / "skills" / name)
            for name in ("third-party-tool", "local-helper")
        }:
            raise AssertionError("unrelated or third-party skills changed")
        for name in bundled_names:
            if tree_manifest(bundle / "skills" / name) != tree_manifest(harness / "skills" / name):
                raise AssertionError(f"installed public skill does not match bundle: {name}")
        if (
            run("git", "rev-parse", "HEAD", cwd=bundle).stdout.strip() != bundle_commit
            or run("git", "status", "--short", cwd=bundle).stdout
        ):
            raise AssertionError("installed materializations do not trace to one bundle commit")

        first_state = full_state(harness, roots, bundle)
        if any("receipt" in path or "run-ledger" in path for path, _digest in tree_manifest(temporary)):
            raise AssertionError("rehearsal persisted a cached receipt or run ledger")

        resumed_repository = json_run(
            "python3",
            str(SETUP_COMMAND),
            "reconcile",
            "--registry",
            str(registry),
            environment=environment,
        )
        for system in SYSTEM_ORDER:
            if system_setup(system, "reconcile", roots[system], harness)["status"] != "converged":
                raise AssertionError(f"live-state resume failed for {system}")
        second_bundle = publish_fixture_bundle(releases, bundle)
        install_bundle(harness, bundle, releases)
        second_automations = reconcile_automations(harness)
        pause_or_resume(harness, True)
        second_state = full_state(harness, roots, bundle)
        if (
            resumed_repository["status"] != "converged"
            or resumed_repository["writes"]
            or second_bundle != "no-op"
            or second_automations["writes"]
            or first_state != second_state
        ):
            raise AssertionError("second identical live-state reconcile was not an exact no-op")

    print("check-migration-rehearsal: ok")


if __name__ == "__main__":
    main()
