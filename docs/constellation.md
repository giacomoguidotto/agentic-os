# Agentic Constellation

This map is intentionally low resolution. It records ownership and composition,
not System internals, provider details, installation state, or release versions.

```mermaid
flowchart LR
  OS["Agentic OS<br/>shared setup, integrations, automations"]
  KS["Knowledge System"]
  MS["Mastery System"]
  CS["Career System"]
  CO["Career Ops<br/>fixed Implementation"]
  DB["Distribution Bundle<br/>generated public projection"]

  OS -->|"System dependency"| KS
  OS -->|"System dependency"| MS
  OS -->|"System dependency"| CS
  CO -->|"implements"| CS
  OS -->|"publishes allowlisted modules"| DB
  KS -.->|"independently usable"| KS
  MS -.->|"independently usable"| MS
  CO -.->|"independently usable"| CO
```

Agentic OS composes Systems only through their public contracts. Setup ordering is
a setup dependency, not ownership. Cross-System calls are integration dependencies,
not permission to store another System's domain model or operational state here.
