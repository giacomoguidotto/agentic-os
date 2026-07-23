#!/usr/bin/env python3
"""Non-publishing Distribution Bundle command for immutable release fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any


EXPECTED_EXPORTS = {
    "giacomoguidotto/agentic-os": ["skills/public/*"],
    "giacomoguidotto/knowledge-system": ["skills/public/*"],
    "giacomoguidotto/mastery-system": ["skills/public/*"],
    "giacomoguidotto/career-system": ["skills/public/setup-career-system"],
}
STABLE_TAG = re.compile(r"^v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    sources = document.get("sources")
    if document.get("schema") != "agentic-os.migration-release-fixtures/v1" or not isinstance(sources, list):
        raise ValueError("invalid immutable release fixture manifest")
    observed = {item.get("repository"): item.get("exports") for item in sources}
    if observed != EXPECTED_EXPORTS:
        raise ValueError("release fixtures violate the locked positive allowlist")
    for source in sources:
        if (
            not STABLE_TAG.fullmatch(source["tag"])
            or not COMMIT.fullmatch(source["commit"])
            or not isinstance(source.get("release_id"), int)
            or source.get("immutable") is not True
        ):
            raise ValueError(f"mutable or unstable release fixture: {source['repository']}")
    return document


def validate_skill(path: Path, expected_name: str) -> None:
    skill = path / "SKILL.md"
    if not skill.is_file():
        raise ValueError(f"malformed skill: {expected_name}")
    declared = next(
        (
            line.split(":", 1)[1].strip()
            for line in skill.read_text(encoding="utf-8").splitlines()
            if line.startswith("name:")
        ),
        None,
    )
    if declared != expected_name:
        raise ValueError(f"skill name mismatch: {expected_name}")
    if any(item.is_symlink() for item in path.rglob("*")):
        raise ValueError(f"skill is not self-contained: {expected_name}")


def candidate(manifest: dict[str, Any], releases: Path, target: Path) -> dict[str, Any]:
    skills = target / "skills"
    skills.mkdir()
    owners: dict[str, str] = {}
    provenance_sources = []
    for source in manifest["sources"]:
        repository = source["repository"]
        release = releases / repository.replace("/", "__")
        public = release / "skills" / "public"
        exports: list[dict[str, str]] = []
        paths = (
            sorted(path for path in public.iterdir() if path.is_dir())
            if source["exports"] == ["skills/public/*"]
            else [release / source["exports"][0]]
        )
        for path in paths:
            name = path.name
            if name in owners:
                raise ValueError(f"skill name collision: {name}")
            validate_skill(path, name)
            shutil.copytree(path, skills / name)
            owners[name] = repository
            exports.append(
                {
                    "name": name,
                    "path": str(path.relative_to(release)),
                    "tree_sha256": tree_digest(path),
                }
            )
        provenance_sources.append(
            {
                "repository": repository,
                "release_id": source["release_id"],
                "tag": source["tag"],
                "commit": source["commit"],
                "archive_sha256": tree_digest(release),
                "exports": exports,
            }
        )
    return {"schema": "distribution-provenance/v1", "sources": provenance_sources}


def same_tree(left: Path, right: Path) -> bool:
    return left.exists() and right.exists() and tree_digest(left) == tree_digest(right)


def reconcile(manifest_path: Path, releases: Path, output: Path) -> str:
    manifest = load_manifest(manifest_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="distribution-candidate-", dir=output.parent) as raw:
        temporary = Path(raw)
        provenance = candidate(manifest, releases, temporary)
        provenance_path = temporary / "provenance.lock.json"
        provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        current_provenance = output / "provenance.lock.json"
        if same_tree(output / "skills", temporary / "skills") and current_provenance.exists() and current_provenance.read_bytes() == provenance_path.read_bytes():
            return "no-op"
        replacement = output.with_name(f".{output.name}.candidate")
        if replacement.exists():
            shutil.rmtree(replacement)
        replacement.mkdir()
        shutil.copytree(temporary / "skills", replacement / "skills")
        shutil.copy2(provenance_path, replacement / "provenance.lock.json")
        if output.exists():
            shutil.rmtree(output)
        replacement.replace(output)
        return "changed"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--releases", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        print(json.dumps({"status": reconcile(arguments.manifest, arguments.releases, arguments.output)}))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "failed", "reason": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
