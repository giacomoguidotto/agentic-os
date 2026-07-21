#!/usr/bin/env python3

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "skills/public/agentic-os"


def load(relative_path):
    with (MODULE / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)


request = load("resources/scout-knowledge-request.json")
schema = load("resources/scout-result.schema.json")
example = load("resources/examples/scout-result.json")

assert request["interface"] == "knowledge-system-interface/v1"
assert request["caller"] == "agentic-os"
assert request["capability"] == "agentic-os.scout"
assert request["clarification_allowed"] is False
assert request["mandate"]["capture_roles"] == []
assert set(request["roles"]["required"]).issubset(request["mandate"]["read_roles"])
assert set(request["roles"]["optional"]).issubset(request["mandate"]["read_roles"])
assert request["intended_use"]["mode"] == "named-sink"
assert request["intended_use"]["target"] == "career-system"

assert schema["$id"] == "agentic-os.scout.result/v1"
properties = schema["properties"]
assert properties["schema"]["const"] == "agentic-os.scout.result/v1"
assert properties["capability"]["const"] == "agentic-os.scout"
assert set(properties["status"]["enum"]) == {"completed", "blocked", "incomplete", "failed"}
assert set(schema["required"]) == set(properties)

assert set(example) == set(schema["required"])
assert example["schema"] == properties["schema"]["const"]
assert example["capability"] == properties["capability"]["const"]
assert example["status"] in properties["status"]["enum"]
assert isinstance(example["requested"], int) and example["requested"] > 0
assert isinstance(example["successful"], int) and example["successful"] >= 0
assert example["successful"] <= example["requested"]
assert set(example["readiness"]) == {"knowledge", "career"}
for evidence in example["readiness"].values():
    assert evidence["status"] in {"ready", "blocked", "failed"}
    assert evidence["observed_at"]
    assert isinstance(evidence["capabilities"], list)
    assert isinstance(evidence["reasons"], list)

skill = (MODULE / "SKILL.md").read_text(encoding="utf-8")
for required_text in (
    "fresh read-only `/setup-knowledge-system check`",
    "career-system.check/v1",
    "career.profile.check/v1",
    "career.profile.reconcile/v1",
    "career.opportunity.discover/v1",
    "Repeat fresh Knowledge readiness, fresh Career readiness",
    "Never roll back a native delta",
    "Never write a profile, snapshot, token, cache, receipt",
    "agentic-os.scout.result/v1",
):
    assert required_text in skill, f"missing scout contract text: {required_text}"

print("agentic-os.scout: OK")
