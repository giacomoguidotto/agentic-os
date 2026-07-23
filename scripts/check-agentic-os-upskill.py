#!/usr/bin/env python3

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "skills/public/agentic-os"


def load(relative_path):
    with (MODULE / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)


def require(condition, message):
    if not condition:
        raise SystemExit(f"agentic-os.upskill: {message}")


schema = load("resources/upskill-result.schema.json")
example = load("resources/examples/upskill-result.json")
blocked_readiness_example = load(
    "resources/examples/upskill-blocked-readiness-result.json"
)

require(
    schema["$id"] == "agentic-os.upskill.result/v1",
    "result schema identifier is invalid",
)
properties = schema["properties"]
require(
    properties["schema"]["const"] == "agentic-os.upskill.result/v1",
    "result schema constant is invalid",
)
require(
    properties["capability"]["const"] == "agentic-os.upskill",
    "result capability constant is invalid",
)
require(
    set(properties["status"]["enum"])
    == {"completed", "blocked", "incomplete", "failed"},
    "terminal status set is invalid",
)
require(
    set(schema["required"]) == set(properties),
    "required result fields do not match declared properties",
)

snapshot_systems = {"career", "knowledge", "mastery"}
snapshot_contract = properties["snapshots"]
require(
    set(snapshot_contract["properties"]) == snapshot_systems,
    "snapshot properties must contain exactly three Systems",
)
require(
    "required" not in snapshot_contract,
    "snapshots acquired before an early block must not be required",
)
require(
    set(properties["snapshot_acquisition"]["enum"])
    == {"not_started", "partial", "completed"},
    "snapshot acquisition states are invalid",
)
snapshot_rules = {
    rule["if"]["properties"]["snapshot_acquisition"]["const"]: rule["then"][
        "properties"
    ]["snapshots"]
    for rule in schema["allOf"]
}
require(
    set(snapshot_rules) == {"not_started", "partial", "completed"},
    "snapshot acquisition rules are incomplete",
)
require(
    snapshot_rules["not_started"]["maxProperties"] == 0,
    "not-started acquisition permits fabricated snapshots",
)
require(
    snapshot_rules["partial"]["minProperties"] == 1
    and snapshot_rules["partial"]["maxProperties"] == 2,
    "partial acquisition does not require one or two snapshots",
)
require(
    set(snapshot_rules["completed"]["required"]) == snapshot_systems,
    "completed acquisition must contain all three snapshots",
)

require(set(example) == set(schema["required"]), "example result fields are invalid")
require(
    example["schema"] == properties["schema"]["const"],
    "example result schema is invalid",
)
require(
    example["capability"] == properties["capability"]["const"],
    "example result capability is invalid",
)
require(
    example["status"] in properties["status"]["enum"],
    "example terminal status is invalid",
)
require(
    example["snapshot_acquisition"] == "completed",
    "complete example snapshot acquisition state is invalid",
)
require(
    set(example["readiness"]) == snapshot_systems,
    "example readiness must contain exactly three Systems",
)
require(
    set(example["snapshots"]) == snapshot_systems,
    "example snapshots must contain exactly three Systems",
)
require(
    {snapshot["schema"] for snapshot in example["snapshots"].values()}
    == {
        "career.requisite.snapshot/v1",
        "knowledge.project.snapshot/v1",
        "mastery.cycles.snapshot/v1",
    },
    "example snapshot schema set is invalid",
)
require(
    all(
        snapshot["revision_checked"] is True
        for snapshot in example["snapshots"].values()
    ),
    "every example snapshot must be revision checked",
)
require(
    [item["rank"] for item in example["ranking"]]
    == list(range(1, len(example["ranking"]) + 1)),
    "example ranks must be contiguous and ordered",
)
require(
    len({item["mapping_key"] for item in example["ranking"]})
    == len(example["ranking"]),
    "example ranking contains duplicate mapping keys",
)
require(
    len({item["mapping_key"] for item in example["mappings"]})
    == len(example["mappings"]),
    "example mapping results contain duplicate mapping keys",
)
ranking_by_key = {
    item["mapping_key"]: item["rank"] for item in example["ranking"]
}
require(
    set(ranking_by_key)
    == {item["mapping_key"] for item in example["mappings"]},
    "example ranking and mapping result keys differ",
)
require(
    all(
        item["rank"] == ranking_by_key[item["mapping_key"]]
        for item in example["mappings"]
    ),
    "example mapping result ranks differ from deterministic ranking",
)
require(
    all(
        item["status"]
        in {
            "created",
            "updated",
            "unchanged",
            "withdrawn",
            "preserved",
            "blocked",
            "failed",
        }
        for item in example["mappings"]
    ),
    "example mapping contains an invalid native terminal status",
)
require(
    isinstance(example["writes"], int) and example["writes"] >= 0,
    "example write count is invalid",
)
if example["status"] == "completed" and example["writes"] == 0:
    require(
        all(
            item["status"] in {"unchanged", "preserved"}
            for item in example["mappings"]
        ),
        "completed no-op example contains a changed mapping",
    )

require(
    set(blocked_readiness_example) == set(schema["required"]),
    "early-blocked example result fields are invalid",
)
require(
    blocked_readiness_example["schema"] == properties["schema"]["const"],
    "early-blocked example result schema is invalid",
)
require(
    blocked_readiness_example["capability"] == properties["capability"]["const"],
    "early-blocked example capability is invalid",
)
require(
    blocked_readiness_example["status"] == "blocked",
    "early-readiness failure must return blocked",
)
require(
    blocked_readiness_example["snapshot_acquisition"] == "not_started",
    "early-blocked snapshot acquisition state is invalid",
)
require(
    set(blocked_readiness_example["readiness"]) == snapshot_systems,
    "early-blocked readiness must contain exactly three Systems",
)
require(
    blocked_readiness_example["snapshots"] == {},
    "early-blocked example fabricates snapshot evidence",
)
require(
    blocked_readiness_example["ranking"] == []
    and blocked_readiness_example["mappings"] == []
    and blocked_readiness_example["writes"] == 0,
    "early-blocked example claims reconciliation work",
)
require(
    blocked_readiness_example["blocked_actions"],
    "early-blocked example lacks a capability-scoped blocker",
)

skill = (MODULE / "SKILL.md").read_text(encoding="utf-8")
for required_text in (
    "/agentic-os upskill <knowledge-project-ref>...",
    "career.requisite.snapshot/v1",
    "knowledge.project.snapshot/v1",
    "mastery.cycles.snapshot",
    "mastery.cycles.reconcile",
    "a status field that a System snapshot contract does not declare",
    "mapping_key` as the sole managed identity",
    "stable topological sort",
    "Verify the full returned graph",
    "report `writes` as zero",
    "`snapshot_acquisition`",
    "never fabricate",
    "never requests capture",
    "agentic-os.upskill.result/v1",
):
    require(
        required_text in skill,
        f"missing upskill contract text: {required_text}",
    )

for prohibited_text in (
    "lib/career-requisite-snapshot.mjs",
    "src/mastery.mjs",
    "produce-project-snapshot.py",
    "Notion",
):
    require(
        prohibited_text not in skill,
        f"upskill contract imports provider or System internals: {prohibited_text}",
    )

print("agentic-os.upskill: OK")
