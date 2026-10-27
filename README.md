![Evaxis logo](https://avatars.githubusercontent.com/u/349042465?v=4)

# Evaxis

**Evidence Across Every Axis.**

Evaxis (EVidence + AXIS) is an independent, provider-neutral security evidence,
provenance, historical analysis and assurance platform in the design stage.
This repository is the future home of its independent core.

## Status and boundaries

**Confirmed:** this is a governance and documentation foundation only.
Evidence collection, storage, assessments, drift processing, hosted services,
authentication and billing are not implemented. There is no product install,
build system, API or release.

Evaxis is not a Maester wrapper or a provider-specific storage/execution layer.
Maester integration is **Proposed**, including possible Maester Packs and
Maester Cloud Plugins. Maester is not the platform's execution or storage
foundation. Provider APIs, structured evidence storage, commercial licensing
and revenue sharing are not established product contracts.

## Design principles

**Confirmed constraints:** provider independence, execution independence,
interchangeable storage, cryptographic flexibility, evidence integrity and
semantic distinction between environmental and evaluator/collection changes.
Useful baseline functionality should not require a paid hosted service;
premium entitlements must not be inseparable from a storage provider.

These are requirements for future design, not implemented assurance guarantees.
See the [foundation boundaries](https://github.com/evaxis/architecture/blob/main/adr/0001-foundation-boundaries.md)
and [initial threat-model scope](https://github.com/evaxis/architecture/blob/main/threat-model/README.md).

## Planned repository contracts

| Path | Status |
|---|---|
| `schemas/evidence/`, `observations/`, `assessments/`, `manifests/` | Planned contracts awaiting specification; no schemas |
| `examples/` | Reserved assessment, incomplete-collection and drift scenarios; no example findings |
| `tests/conformance/` | Planned conformance work; no test implementation |

Start with [design-stage orientation](docs/getting-started.md).
The [architecture repository](https://github.com/evaxis/architecture) records
principles, decisions and [roadmap](https://github.com/evaxis/architecture/blob/main/roadmap/README.md).

## Contributing and security

Read [contribution guidance](CONTRIBUTING.md) and [security reporting](SECURITY.md).
Canonical cARL governance is under `.github/carl/`; generated harness adapters
load it. Bundled cloud/language packs are inactive, not technology decisions.

**Undecided:** implementation language, build system, execution model, backend,
cloud, detailed contracts and licensing. Public visibility does not mean
licensed open source. No Evaxis licence is selected; do not introduce
substantial implementation before that decision. Upstream cARL assets retain
their own licence in [third-party notices](THIRD_PARTY_NOTICES.md).
