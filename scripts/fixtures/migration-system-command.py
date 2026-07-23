#!/usr/bin/env python3
"""Executable System release fixture used only by the migration rehearsal."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


def read_input() -> dict[str, Any]:
    if sys.stdin.isatty():
        return {}
    text = sys.stdin.read()
    return json.loads(text) if text.strip() else {}


def read_json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def write_json_if_changed(path: Path, document: Any) -> list[str]:
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    if path.exists() and path.read_bytes() == payload:
        return []
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.candidate")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return [str(path)]


def copy_tree_if_changed(source: Path, target: Path) -> list[str]:
    desired = {
        str(path.relative_to(source)): path.read_bytes()
        for path in sorted(source.rglob("*"))
        if path.is_file()
    }
    actual = (
        {
            str(path.relative_to(target)): path.read_bytes()
            for path in sorted(target.rglob("*"))
            if path.is_file()
        }
        if target.exists()
        else {}
    )
    if actual == desired:
        return []
    candidate = target.with_name(f".{target.name}.candidate")
    if candidate.exists():
        shutil.rmtree(candidate)
    shutil.copytree(source, candidate)
    if target.exists():
        shutil.rmtree(target)
    candidate.replace(target)
    return [str(target)]


def setup_knowledge(mode: str, root: Path, harness: Path) -> dict[str, Any]:
    bindings = root / "local" / "bindings.yml"
    interface = harness / "skills" / "knowledge-system-interface" / "v1"
    desired = root / "release" / "knowledge-system-interface" / "v1"
    writes: list[str] = []
    drifted = not interface.exists() or tree_digest(interface) != tree_digest(desired)
    if mode == "reconcile" and drifted:
        writes.extend(copy_tree_if_changed(desired, interface))
    status = "converged" if interface.exists() and tree_digest(interface) == tree_digest(desired) else "drifted"
    return {
        "schema": "knowledge.setup.result/v1",
        "mode": mode,
        "status": status,
        "writes": writes,
        "branches": {
            "bindings": "converged" if bindings.exists() else "blocked",
            "interface": status,
            "kb_reconcile": "converged"
        },
        "capabilities": {
            "snapshot-token-validation": "ready" if status == "converged" else "blocked",
            "knowledge-project-snapshot": "ready" if status == "converged" else "blocked"
        }
    }


def setup_career(mode: str, root: Path, _harness: Path) -> dict[str, Any]:
    template = root / "modes" / "_profile.template.md"
    profile = root / "modes" / "_profile.md"
    writes: list[str] = []
    if mode == "reconcile" and not profile.exists():
        profile.write_bytes(template.read_bytes())
        writes.append(str(profile))
    import_ready = (root / "main.mjs").exists()
    operational_ready = import_ready and profile.exists()
    return {
        "schema": "career-system.setup.result/v1",
        "mode": mode,
        "status": "converged" if operational_ready else "blocked",
        "changed": writes,
        "import_ready": {"status": "ready" if import_ready else "blocked"},
        "operational_ready": {"status": "ready" if operational_ready else "blocked"}
    }


def setup_mastery(mode: str, root: Path, _harness: Path) -> dict[str, Any]:
    readiness = root / "state" / "tracker-readiness.json"
    desired = {"issues": True, "labels": "canonical", "template": "ready"}
    drifted = read_json(readiness, {}) != desired
    writes = write_json_if_changed(readiness, desired) if mode == "reconcile" and drifted else []
    return {
        "schema": "mastery.setup.result/v1",
        "capability": "mastery.setup",
        "mode": mode,
        "status": "converged" if read_json(readiness, {}) == desired else "drifted",
        "actions": writes
    }


def setup(system: str, mode: str, root: Path, harness: Path) -> dict[str, Any]:
    return {
        "knowledge": setup_knowledge,
        "career": setup_career,
        "mastery": setup_mastery,
    }[system](mode, root, harness)


def knowledge_gateway(capability: str, root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    revision = (root / "state" / "knowledge-revision").read_text(encoding="utf-8").strip()
    if capability == "knowledge.snapshot/v1":
        requested = payload.get("roles", [])
        allowed = {"identity", "selected-projects", "public-safe-claim-source"}
        invalid = sorted(set(requested) - allowed)
        if invalid:
            return {
                "schema": "knowledge.snapshot/v1",
                "status": "blocked",
                "capability": payload.get("capability"),
                "reasons": [f"unknown-role:{role}" for role in invalid]
            }
        token = hashlib.sha256(f"opaque:{revision}:{','.join(sorted(requested))}".encode()).hexdigest()
        return {
            "schema": "knowledge.snapshot/v1",
            "status": "ready",
            "capability": payload.get("capability"),
            "registry_revision": revision,
            "snapshot_token": token,
            "results": [
                {
                    "role": role,
                    "state": "value",
                    "claims": [{"value": f"fixture:{role}", "visibility": "public-safe"}],
                    "evidence": [{"kind": "fixture-release", "revision": revision}],
                    "provenance": [{"owner": "canonical-knowledge-owner"}]
                }
                for role in requested
            ]
        }
    if capability == "knowledge.snapshot-token.validate/v1":
        expected = knowledge_gateway(
            "knowledge.snapshot/v1",
            root,
            {"roles": payload.get("roles", []), "capability": payload.get("capability")},
        )["snapshot_token"]
        return {
            "schema": "knowledge.snapshot-token-validation.result/v1",
            "status": "unchanged" if payload.get("snapshot_token") == expected else "changed"
        }
    if capability == "knowledge.capture/v1":
        return {
            "schema": "knowledge.capture-blocked/v1",
            "status": "blocked",
            "reason": "explicit-capture-approval-required",
            "operations": []
        }
    raise ValueError(f"unsupported Knowledge capability: {capability}")


def career_gateway(capability: str, root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    profile = root / "config" / "career-profile.json"
    if capability == "career.profile.check/v1":
        desired = payload.get("profile", {})
        return {
            "schema": "career.profile.check.result/v1",
            "status": "ready",
            "drift": read_json(profile, {}) != desired
        }
    if capability == "career.profile.reconcile/v1":
        desired = payload.get("profile", {})
        writes = write_json_if_changed(profile, desired)
        return {
            "schema": "career.profile.reconcile.result/v1",
            "status": "converged",
            "writes": writes,
            "revision": payload.get("revision")
        }
    if capability == "career-system.check/v1":
        requested = payload.get("capabilities", [])
        return {
            "schema": "career-system.check.result/v1",
            "status": "ready",
            "result": {
                "capabilities": [
                    {"capability": item, "status": "ready"} for item in requested
                ]
            }
        }
    raise ValueError(f"unsupported Career capability: {capability}")


def mastery_gateway(capability: str, root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    cycles = root / "state" / "cycles.json"
    document = read_json(cycles, {"cycles": [], "history": ["pre-migration-assessment"]})
    if capability == "mastery.cycles.snapshot/v1":
        return {"schema": "mastery.cycles.snapshot/v1", "status": "ready", **document}
    if capability == "mastery.cycles.reconcile/v1":
        by_key = {item["mapping_key"]: item for item in document["cycles"]}
        for mapping in payload.get("mappings", []):
            by_key.setdefault(
                mapping["mapping_key"],
                {
                    "mapping_key": mapping["mapping_key"],
                    "cycle_id": f"cycle:{mapping['mapping_key']}",
                    "status": "proposed",
                    "dependencies": sorted(mapping.get("dependencies", []))
                },
            )
        updated = {"cycles": sorted(by_key.values(), key=lambda item: item["mapping_key"]), "history": document["history"]}
        writes = write_json_if_changed(cycles, updated)
        return {
            "schema": "mastery.cycles.reconcile/v1",
            "status": "converged",
            "writes": writes,
            **updated
        }
    raise ValueError(f"unsupported Mastery capability: {capability}")


def gateway(system: str, capability: str, root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "knowledge": knowledge_gateway,
        "career": career_gateway,
        "mastery": mastery_gateway,
    }[system](capability, root, payload)


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    if not root.exists():
        return ""
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="command", required=True)
    setup_parser = subcommands.add_parser("setup")
    setup_parser.add_argument("system", choices=("knowledge", "mastery", "career"))
    setup_parser.add_argument("mode", choices=("check", "reconcile"))
    setup_parser.add_argument("--root", required=True, type=Path)
    setup_parser.add_argument("--harness", required=True, type=Path)
    gateway_parser = subcommands.add_parser("gateway")
    gateway_parser.add_argument("system", choices=("knowledge", "mastery", "career"))
    gateway_parser.add_argument("capability")
    gateway_parser.add_argument("--root", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        if arguments.command == "setup":
            result = setup(arguments.system, arguments.mode, arguments.root, arguments.harness)
        else:
            result = gateway(arguments.system, arguments.capability, arguments.root, read_input())
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "failed", "reason": str(error)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
