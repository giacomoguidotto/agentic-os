#!/usr/bin/env python3
"""Exercise the public setup contract at observable seams."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch


sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parent.parent
SETUP_PATH = (
    REPO_ROOT
    / "skills"
    / "public"
    / "setup-agentic-os"
    / "scripts"
    / "setup-agentic-os.py"
)
AUTOMATION_TOOL = SETUP_PATH.with_name("reconcile-automation-sources.py")


def command(*arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def load_setup():
    spec = importlib.util.spec_from_file_location("setup_agentic_os", SETUP_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load setup module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_automation_tool():
    spec = importlib.util.spec_from_file_location(
        "reconcile_automation_sources", AUTOMATION_TOOL
    )
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load automation reconciliation module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def create_repository(
    temporary: Path,
    contract: dict,
) -> Path:
    key = contract["registry_key"]
    bare = temporary / f"{key}.git"
    seed = temporary / f"{key}-seed"
    root = temporary / key
    command("git", "init", "--bare", str(bare))
    command("git", "init", str(seed))
    command("git", "config", "user.name", "Setup Test", cwd=seed)
    command("git", "config", "user.email", "setup@example.invalid", cwd=seed)
    for required in contract["required_paths"]:
        path = seed / required
        if Path(required).suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)
            (path / ".fixture").write_text("fixture\n", encoding="utf-8")
    command("git", "add", ".", cwd=seed)
    command("git", "commit", "-m", "test: setup fixture", cwd=seed)
    command("git", "branch", "-M", contract["required_branch"], cwd=seed)
    command("git", "remote", "add", "origin", str(bare), cwd=seed)
    command(
        "git",
        "push",
        "-u",
        "origin",
        contract["required_branch"],
        cwd=seed,
    )
    command(
        "git",
        "clone",
        "--branch",
        contract["required_branch"],
        str(bare),
        str(root),
    )
    public_url = f"https://github.com/{contract['repository']}.git"
    command("git", "remote", "set-url", "origin", public_url, cwd=root)
    return root


def main() -> None:
    setup = load_setup()
    contracts = setup.load_contracts()
    if [item["registry_key"] for item in contracts] != [
        "knowledge-system",
        "mastery-system",
        "career-ops",
    ]:
        raise AssertionError("fixed System contract changed")
    if setup.trusted_github_host(
        "https://attacker.invalid/giacomoguidotto/knowledge-system.git"
    ):
        raise AssertionError("repository identity accepted an untrusted remote host")

    with tempfile.TemporaryDirectory() as raw_temporary:
        temporary = Path(raw_temporary)
        roots = {
            contract["registry_key"]: create_repository(temporary, contract)
            for contract in contracts
        }
        registry = temporary / "installation.yml"
        registry.write_text(
            "repositories:\n"
            + "".join(f"  {key}: {roots[key]}\n" for key in setup.EXPECTED_REGISTRY_KEYS),
            encoding="utf-8",
        )
        parsed = setup.parse_registry(registry)
        if parsed != roots:
            raise AssertionError("roots-only registry did not round-trip")

        original_run = setup.run

        def fixture_run(arguments, *, cwd=None, check=False):
            if arguments[:2] == ["git", "ls-remote"]:
                head = original_run(["git", "rev-parse", "HEAD"], cwd=cwd)
                return subprocess.CompletedProcess(
                    arguments,
                    head.returncode,
                    f"{head.stdout.strip()}\t{arguments[-1]}\n",
                    head.stderr,
                )
            return original_run(arguments, cwd=cwd, check=check)

        with patch.object(setup, "run", side_effect=fixture_run):
            before = {key: tree_digest(root) for key, root in roots.items()}
            checked = setup.execute("check", registry)
            after = {key: tree_digest(root) for key, root in roots.items()}
            if checked["status"] != "converged" or checked["writes"] or before != after:
                raise AssertionError(
                    f"check was not a read-only converged observation: {checked}"
                )

            first = setup.execute("reconcile", registry)
            second = setup.execute("reconcile", registry)
            if (
                first["status"] != "converged"
                or second["status"] != "converged"
                or first["writes"]
                or second["writes"]
            ):
                raise AssertionError(
                    "identical repository reconcile was not a zero-write no-op"
                )

            dirty_root = roots["mastery-system"]
            dirty_path = dirty_root / "untracked-user-work"
            dirty_path.write_text("preserve\n", encoding="utf-8")
            dirty_head = command("git", "rev-parse", "HEAD", cwd=dirty_root).stdout
            blocked = setup.execute("reconcile", registry)
            if (
                blocked["status"] != "blocked"
                or next(
                    branch
                    for branch in blocked["branches"]
                    if branch["key"] == "mastery-system"
                )["reason"]
                != "dirty-worktree"
                or command("git", "rev-parse", "HEAD", cwd=dirty_root).stdout
                != dirty_head
                or dirty_path.read_text(encoding="utf-8") != "preserve\n"
            ):
                raise AssertionError("unsafe Git state was mutated or not isolated")
            dirty_path.unlink()

            missing_registry = temporary / "missing-installation.yml"
            missing_root = temporary / "missing-parent" / "knowledge-system"
            missing_registry.write_text(
                "repositories:\n"
                f"  knowledge-system: {missing_root}\n"
                f"  mastery-system: {roots['mastery-system']}\n"
                f"  career-ops: {roots['career-ops']}\n",
                encoding="utf-8",
            )
            failed_clone = setup.execute("reconcile", missing_registry)
            knowledge_branch = next(
                branch
                for branch in failed_clone["branches"]
                if branch["key"] == "knowledge-system"
            )
            if (
                knowledge_branch["status"] != "blocked"
                or knowledge_branch["reason"] != "registered-root-parent-missing"
            ):
                raise AssertionError("failed clone attempt remained reported as drift")

            long_registry = temporary / "long-installation.yml"
            long_root = temporary / ("k" * 250)
            long_registry.write_text(
                "repositories:\n"
                f"  knowledge-system: {long_root}\n"
                f"  mastery-system: {roots['mastery-system']}\n"
                f"  career-ops: {roots['career-ops']}\n",
                encoding="utf-8",
            )
            clone_exception = setup.execute("reconcile", long_registry)
            long_branches = {
                branch["key"]: branch for branch in clone_exception["branches"]
            }
            if (
                long_branches["knowledge-system"]["reason"]
                != "clone-filesystem-error"
                or long_branches["mastery-system"]["status"] != "converged"
                or long_branches["career-ops"]["status"] != "converged"
            ):
                raise AssertionError("clone exception stopped independent branches")

        rewrite_root = roots["knowledge-system"]
        configured = (
            "https://github.com/giacomoguidotto/knowledge-system.git"
        )
        command(
            "git",
            "config",
            f"url.file://{temporary}/knowledge-system.git/.insteadOf",
            configured,
            cwd=rewrite_root,
        )
        rewritten = setup.observe_repository(contracts[0], rewrite_root)
        if rewritten["reason"] != "wrong-repository-identity":
            raise AssertionError("effective Git transport bypassed remote trust")

        malformed = temporary / "malformed.yml"
        malformed.write_text(
            registry.read_text(encoding="utf-8") + "  feature-flag: true\n",
            encoding="utf-8",
        )
        if setup.execute("check", malformed)["status"] != "failed":
            raise AssertionError("registry accepted non-root installation state")

        source_lane = temporary / "automation-sources"
        first_run = json.loads(
            command(
                "python3",
                str(AUTOMATION_TOOL),
                "reconcile",
                "--target-root",
                str(source_lane),
            ).stdout
        )
        first_digest = tree_digest(source_lane)
        second_run = json.loads(
            command(
                "python3",
                str(AUTOMATION_TOOL),
                "reconcile",
                "--target-root",
                str(source_lane),
            ).stdout
        )
        if (
            first_run["status"] != "converged"
            or not first_run["writes"]
            or second_run["status"] != "converged"
            or second_run["writes"]
            or tree_digest(source_lane) != first_digest
        ):
            raise AssertionError("automation source reconciliation is not idempotent")

        outside = temporary / "outside"
        outside.mkdir()
        protected = outside / "prompt.md"
        protected.write_text("preserve\n", encoding="utf-8")
        unsafe_lane = temporary / "unsafe-automation-sources"
        unsafe_lane.mkdir()
        (unsafe_lane / "job-scout").symlink_to(outside, target_is_directory=True)
        unsafe = subprocess.run(
            [
                "python3",
                str(AUTOMATION_TOOL),
                "reconcile",
                "--target-root",
                str(unsafe_lane),
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if unsafe.returncode == 0 or protected.read_text(encoding="utf-8") != "preserve\n":
            raise AssertionError("automation reconciliation followed a target symlink")

        escaped = temporary / "escaped"
        malicious = [
            {
                "name": "../escaped",
                "source": "automations/job-scout",
                "stable_identity": "escape",
            }
        ]
        try:
            setup_lane = load_automation_tool()
            setup_lane.reconcile(malicious, unsafe_lane)
        except ValueError:
            pass
        else:
            raise AssertionError("automation name escaped the target root")
        if escaped.exists():
            raise AssertionError("path traversal created files outside the target root")

    print("check-setup-agentic-os: ok")


if __name__ == "__main__":
    main()
