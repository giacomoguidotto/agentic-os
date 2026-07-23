#!/usr/bin/env python3

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "skills/public/agentic-os"


def load(relative_path):
    with (MODULE / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)


request = load("resources/pursue-knowledge-request.json")
schema = load("resources/pursue-result.schema.json")
example = load("resources/examples/pursue-result.json")

assert request["interface"] == "knowledge-system-interface/v1"
assert request["caller"] == "agentic-os"
assert request["capability"] == "agentic-os.pursue"
assert request["clarification_allowed"] is False
assert request["mandate"]["capture_roles"] == []
assert set(request["roles"]["required"]).issubset(request["mandate"]["read_roles"])
assert set(request["roles"]["optional"]).issubset(request["mandate"]["read_roles"])
assert request["roles"]["optional"] == ["communication-strategy"]
assert request["intended_use"]["mode"] == "named-sink"
assert request["intended_use"]["target"] == "career-system"

assert schema["$id"] == "agentic-os.pursue.result/v1"
properties = schema["properties"]
assert properties["schema"]["const"] == "agentic-os.pursue.result/v1"
assert properties["capability"]["const"] == "agentic-os.pursue"
assert set(properties["status"]["enum"]) == {"completed", "blocked", "incomplete", "failed"}
assert set(properties["personalization"]["enum"]) == {"personalized", "generic-defaults"}
assert set(schema["required"]) == set(properties)

assert set(example) == set(schema["required"])
assert example["schema"] == properties["schema"]["const"]
assert example["capability"] == properties["capability"]["const"]
assert example["status"] in properties["status"]["enum"]
assert example["personalization"] in properties["personalization"]["enum"]
assert set(example["readiness"]) == {"knowledge", "career"}
for evidence in example["readiness"].values():
    assert evidence["status"] in {"ready", "blocked", "failed"}
    assert evidence["observed_at"]
    assert isinstance(evidence["capabilities"], list)
    assert isinstance(evidence["reasons"], list)

for key in ("selected", "plans", "draft_packs"):
    assert isinstance(example[key], list)
    assert all(isinstance(reference, str) and reference for reference in example[key])
for key in (
    "suppressed",
    "research_blocked",
    "wait_recommendations",
    "safe_advances",
    "required_approvals",
    "proposed_captures",
    "blocked_actions",
):
    assert isinstance(example[key], list)
    for summary in example[key]:
        assert set(summary).issubset({"code", "message", "reference"})
        assert summary["code"] and summary["message"]

skill = (MODULE / "SKILL.md").read_text(encoding="utf-8")
for required_text in (
    "/agentic-os pursue",
    "fresh read-only `/setup-knowledge-system check`",
    "career.opportunity.select-related/v1",
    "career.opportunity.advance/v1",
    "career.opportunity.review-waiting/v1",
    "generic-defaults",
    "Never submit an application",
    "assert a reply or external outcome",
    "agentic-os.pursue.result/v1",
):
    assert required_text in skill, f"missing pursue contract text: {required_text}"

prohibited_direct_access = (
    "candidacy-select.mjs",
    "batch-runner",
    "tracker.mjs",
    "/career-ops next",
)
for text in prohibited_direct_access:
    assert text not in skill, f"pursue contract invokes Career internal: {text}"

print("agentic-os.pursue: OK")
