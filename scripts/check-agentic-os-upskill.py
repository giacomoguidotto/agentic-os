#!/usr/bin/env python3

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "skills/public/agentic-os"


def load(relative_path):
    with (MODULE / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)


schema = load("resources/upskill-result.schema.json")
example = load("resources/examples/upskill-result.json")

assert schema["$id"] == "agentic-os.upskill.result/v1"
properties = schema["properties"]
assert properties["schema"]["const"] == "agentic-os.upskill.result/v1"
assert properties["capability"]["const"] == "agentic-os.upskill"
assert set(properties["status"]["enum"]) == {
    "completed",
    "blocked",
    "incomplete",
    "failed",
}
assert set(schema["required"]) == set(properties)

assert set(example) == set(schema["required"])
assert example["schema"] == properties["schema"]["const"]
assert example["capability"] == properties["capability"]["const"]
assert example["status"] in properties["status"]["enum"]
assert set(example["readiness"]) == {"career", "knowledge", "mastery"}
assert set(example["snapshots"]) == {"career", "knowledge", "mastery"}
assert {
    snapshot["schema"] for snapshot in example["snapshots"].values()
} == {
    "career.requisite.snapshot/v1",
    "knowledge.project.snapshot/v1",
    "mastery.cycles.snapshot/v1",
}
assert all(snapshot["revision_checked"] is True for snapshot in example["snapshots"].values())
assert [item["rank"] for item in example["ranking"]] == list(
    range(1, len(example["ranking"]) + 1)
)
assert len({item["mapping_key"] for item in example["ranking"]}) == len(
    example["ranking"]
)
assert len({item["mapping_key"] for item in example["mappings"]}) == len(
    example["mappings"]
)
assert isinstance(example["writes"], int) and example["writes"] >= 0
if example["status"] == "completed" and example["writes"] == 0:
    assert all(
        item["status"] in {"unchanged", "preserved"} for item in example["mappings"]
    )

skill = (MODULE / "SKILL.md").read_text(encoding="utf-8")
for required_text in (
    "/agentic-os upskill <knowledge-project-ref>...",
    "career.requisite.snapshot/v1",
    "knowledge.project.snapshot/v1",
    "mastery.cycles.snapshot",
    "mastery.cycles.reconcile",
    "mapping_key` as the sole managed identity",
    "stable topological sort",
    "Verify the full returned graph",
    "report `writes` as zero",
    "never requests capture",
    "agentic-os.upskill.result/v1",
):
    assert required_text in skill, f"missing upskill contract text: {required_text}"

for prohibited_text in (
    "lib/career-requisite-snapshot.mjs",
    "src/mastery.mjs",
    "produce-project-snapshot.py",
    "Notion",
):
    assert prohibited_text not in skill, (
        f"upskill contract imports provider or System internals: {prohibited_text}"
    )

print("agentic-os.upskill: OK")
