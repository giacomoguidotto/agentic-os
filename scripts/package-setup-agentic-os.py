#!/usr/bin/env python3
"""Package canonical automation sources into the distributed setup skill."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = REPOSITORY_ROOT / "automations"
SOURCE_MANIFEST = SOURCE_ROOT / "manifest.json"
DEFAULT_SKILL_ROOT = (
    REPOSITORY_ROOT / "skills" / "public" / "setup-agentic-os"
)
MARKER_NAME = "AUTOMATIONS.generated.md"
PACKAGED_MANIFEST_NAME = "automation-migration.json"
MARKER_CONTENT = """# Generated automation resources

Do not edit the automation files in this installed or packaged skill.

Their canonical source is the `automations/` module in the Agentic OS source
repository. Release packaging projects that module here so
`setup-agentic-os` remains self-contained after distribution.
"""


def load_manifest() -> list[dict[str, Any]]:
    document = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    automations = document.get("automations")
    if (
        document.get("schema") != "agentic-os.automation-migration/v1"
        or not isinstance(automations, list)
        or not automations
    ):
        raise ValueError("invalid canonical automation manifest")

    names: list[str] = []
    identities: list[str] = []
    for automation in automations:
        name = automation.get("name")
        identity = automation.get("stable_identity")
        source = automation.get("source")
        if not isinstance(name, str) or source != f"automations/{name}":
            raise ValueError(f"invalid canonical automation entry: {name}")
        if not isinstance(identity, str) or not identity:
            raise ValueError(f"automation lacks stable identity: {name}")
        source_root = REPOSITORY_ROOT / source
        if not source_root.is_dir() or source_root.is_symlink():
            raise ValueError(f"automation source is missing or unsafe: {source}")
        if not (source_root / "automation.toml").is_file():
            raise ValueError(f"automation definition is missing: {source}")
        if any(item.is_symlink() for item in source_root.rglob("*")):
            raise ValueError(f"automation source contains a symlink: {source}")
        names.append(name)
        identities.append(identity)

    if len(set(names)) != len(names) or len(set(identities)) != len(identities):
        raise ValueError("automation names and stable identities must be unique")

    observed = sorted(
        item.parent.name
        for item in SOURCE_ROOT.glob("*/automation.toml")
        if item.is_file()
    )
    if observed != sorted(names):
        raise ValueError("canonical automation manifest and source directories differ")
    return automations


def generated_paths(skill_root: Path) -> tuple[Path, Path, Path]:
    resources = skill_root / "resources"
    return (
        resources / MARKER_NAME,
        resources / PACKAGED_MANIFEST_NAME,
        resources / "automations",
    )


def require_skill_root(skill_root: Path) -> None:
    skill_file = skill_root / "SKILL.md"
    if not skill_file.is_file() or "name: setup-agentic-os" not in skill_file.read_text(
        encoding="utf-8"
    ):
        raise ValueError(f"not a setup-agentic-os skill root: {skill_root}")
    if not (skill_root / "resources" / "system-contracts.json").is_file():
        raise ValueError(f"setup skill lacks System contracts: {skill_root}")


def copy_automation_sources(destination: Path, automations: list[dict[str, Any]]) -> None:
    destination.mkdir()
    for automation in automations:
        name = automation["name"]
        shutil.copytree(SOURCE_ROOT / name, destination / name)


def materialize(skill_root: Path) -> None:
    skill_root = skill_root.resolve()
    require_skill_root(skill_root)
    automations = load_manifest()
    marker, packaged_manifest, packaged_automations = generated_paths(skill_root)
    resources = skill_root / "resources"

    has_packaged_automations = packaged_automations.is_symlink() or (
        packaged_automations.is_dir()
        and any(
            item.is_file() or item.is_symlink()
            for item in packaged_automations.rglob("*")
        )
    )
    has_generated_output = packaged_manifest.exists() or has_packaged_automations
    if (
        marker.is_symlink()
        or packaged_manifest.is_symlink()
        or packaged_automations.is_symlink()
    ):
        raise ValueError("refusing to replace symlinked setup automation resources")
    if packaged_automations.exists() and not packaged_automations.is_dir():
        raise ValueError("packaged automation resources must be a directory")
    if packaged_manifest.exists() and not packaged_manifest.is_file():
        raise ValueError("packaged automation manifest must be a file")
    if marker.exists() and not marker.is_file():
        raise ValueError("generated automation marker must be a file")
    if has_generated_output and (
        not marker.is_file()
        or marker.read_text(encoding="utf-8") != MARKER_CONTENT
    ):
        raise ValueError("refusing to replace unmarked setup automation resources")

    with tempfile.TemporaryDirectory(
        prefix=".automation-package-", dir=resources
    ) as raw_temporary:
        candidate = Path(raw_temporary)
        candidate_automations = candidate / "automations"
        copy_automation_sources(candidate_automations, automations)
        candidate_manifest = candidate / PACKAGED_MANIFEST_NAME
        shutil.copyfile(SOURCE_MANIFEST, candidate_manifest)

        replacement = resources / ".automations.candidate"
        if replacement.exists():
            shutil.rmtree(replacement)
        candidate_automations.replace(replacement)
        if packaged_automations.exists():
            shutil.rmtree(packaged_automations)
        replacement.replace(packaged_automations)
        candidate_manifest.replace(packaged_manifest)

    marker.write_text(MARKER_CONTENT, encoding="utf-8")
    verify(skill_root)


def file_manifest(root: Path) -> dict[str, bytes]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"generated automation directory is missing or unsafe: {root}")
    if any(item.is_symlink() for item in root.rglob("*")):
        raise ValueError(f"generated automation directory contains a symlink: {root}")
    return {
        str(item.relative_to(root)): item.read_bytes()
        for item in sorted(path for path in root.rglob("*") if path.is_file())
    }


def verify(skill_root: Path) -> None:
    skill_root = skill_root.resolve()
    require_skill_root(skill_root)
    automations = load_manifest()
    marker, packaged_manifest, packaged_automations = generated_paths(skill_root)
    if marker.read_text(encoding="utf-8") != MARKER_CONTENT:
        raise ValueError("generated automation marker is missing or stale")
    if packaged_manifest.read_bytes() != SOURCE_MANIFEST.read_bytes():
        raise ValueError("packaged automation manifest differs from canonical source")

    expected: dict[str, bytes] = {}
    for automation in automations:
        name = automation["name"]
        source = SOURCE_ROOT / name
        for item in sorted(path for path in source.rglob("*") if path.is_file()):
            expected[str(Path(name) / item.relative_to(source))] = item.read_bytes()
    if file_manifest(packaged_automations) != expected:
        raise ValueError("packaged automation sources differ from canonical source")


def check() -> None:
    load_manifest()
    marker, packaged_manifest, packaged_automations = generated_paths(
        DEFAULT_SKILL_ROOT
    )
    has_packaged_automations = packaged_automations.is_symlink() or (
        packaged_automations.is_dir()
        and any(
            item.is_file() or item.is_symlink()
            for item in packaged_automations.rglob("*")
        )
    )
    if marker.exists() or packaged_manifest.exists() or has_packaged_automations:
        raise ValueError(
            "generated automation resources must not be committed on the source branch"
        )

    with tempfile.TemporaryDirectory(
        prefix="setup-agentic-os-package-check-"
    ) as raw_temporary:
        temporary = Path(raw_temporary)
        packaged_skill = temporary / "setup-agentic-os"
        shutil.copytree(DEFAULT_SKILL_ROOT, packaged_skill)
        materialize(packaged_skill)
        lane = temporary / "automation-sources"
        command = packaged_skill / "scripts" / "reconcile-automation-sources.py"
        first = subprocess.run(
            [
                sys.executable,
                str(command),
                "reconcile",
                "--target-root",
                str(lane),
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        second = subprocess.run(
            [
                sys.executable,
                str(command),
                "reconcile",
                "--target-root",
                str(lane),
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
        first_result = json.loads(first.stdout)
        second_result = json.loads(second.stdout)
        if not first_result["writes"] or second_result["writes"]:
            raise ValueError("packaged automation reconciliation is not idempotent")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("check", "materialize", "verify"))
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=DEFAULT_SKILL_ROOT,
        help="setup-agentic-os skill root to package or verify",
    )
    arguments = parser.parse_args()
    try:
        if arguments.mode == "check":
            if arguments.skill_root.resolve() != DEFAULT_SKILL_ROOT.resolve():
                parser.error("--skill-root is not supported in check mode")
            check()
        elif arguments.mode == "materialize":
            materialize(arguments.skill_root)
        else:
            verify(arguments.skill_root)
        print(f"package-setup-agentic-os: {arguments.mode} ok")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"package-setup-agentic-os: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
