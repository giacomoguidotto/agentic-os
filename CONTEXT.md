# Agentic OS

## Canonical vocabulary

**Agentic Constellation**: The complete arrangement of Agentic OS and the
independently usable Systems it coordinates.

**Agentic OS**: The public-safe source and specification repository for shared
setup, cross-System integrations, cross-System automations, and generated
distribution policy. It is not a running control plane.

**System**: An independently clonable, releasable, settable up, validatable, and
usable agent product with its own domain ownership and operational state.

**Implementation**: The fixed concrete product that fulfills a System role. An
Implementation is not selected through a runtime plugin registry.

**System dependency**: A dependency on a System's independently usable public
contract.

**Integration dependency**: A dependency required only when Agentic OS composes
behavior across two or more Systems.

**Setup dependency**: Ordering required to materialize or validate an integration.
It does not transfer ownership between repositories.

**Materialization**: An installed skill, configured automation, or other live
artifact produced from a committed source definition. Runtime state belongs to
the materialization environment, not this repository.

**Distribution Bundle**: A generated, allowlisted projection of public release
modules. It has its own publication history and does not coordinate System
versions.

## Ownership rule

The narrowest domain that fully explains a definition owns it. Agentic OS owns a
definition only when correct behavior requires cross-System knowledge or
constellation-wide policy. A System remains independently usable without Agentic
OS.
