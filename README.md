![Evaxis logo](https://avatars.githubusercontent.com/u/349042465?v=4)

# Evaxis

**Evidence Across Every Axis.**

Evaxis (EVidence + AXIS) is an independent, provider-neutral security evidence,
provenance, historical analysis and assurance platform in the design stage.
This repository is the future home of its independent core.

## Status and boundaries

**Confirmed:** this is a design/governance foundation with proposed schemas,
validation tooling and a separately authorized **synthetic evidence-preservation
experiment**. A reusable helper captures source facts before a real
Maester-native assessment and produces a validated v0.1 package.
No provider-connected collection, storage service, drift processing, hosted
service, authentication, billing, product installation or release exists.

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

## Contracts and experimental proof

| Path | Status |
|---|---|
| `schemas/{evidence,observations,assessments,manifests}/` | Proposed modular Evidence Envelope v0.1 JSON Schemas; pending architecture review |
| `tests/conformance/` | Structural fixtures, package-consistency rejection cases, and semantic expectations with preconditions; no comparison engine |
| `tools/validate_conformance.py` | Validation-only tooling; not a product runtime or comparison engine |
| `capture/` | Experimental provider-neutral capture `0.1`, local assembly and multi-record validation; separate from Envelope schemas |
| `integrations/powershell/` | Replaceable explicit-session helper; usable without Maester |
| `integrations/maester/` | Optional pinned synthetic native callback and execution-associated export, not a Pack or generic result importer |
| `examples/evidence-preservation/` and `tests/capture/` | Genuinely generated golden package, offline invocation, and executable positive/adversarial tests |
| `docs/maester-compatibility.md` | Source-verified research plus the bounded native proof; ordinary verdict rows still cannot reconstruct evidence |
| `tools/ci/` and `.github/workflows/capture-validation.yml` | Isolated, integrity-checked Windows/Linux synthetic validation; measured configurations and residual limits, not production assurance |

The [human-semantic Evidence Envelope v0.1 proposal](https://github.com/evaxis/architecture/blob/main/specifications/evidence-envelope-v0.1.md)
is authoritative for terminology and intended meaning. This repository owns
machine-readable structure and synthetic conformance data. Both remain
proposals until reviewed and explicitly approved; the contract version is
`0.1`. Producer-supplied integrity/authentication fields are claims, not
receiver-established trust. See [validation instructions](tests/conformance/README.md).

Start with [design-stage orientation](docs/getting-started.md).
Reproduce the [synthetic/offline proof](docs/evidence-preservation.md) and read
its explicit supported/unsupported boundary. The distinct
[preservation proposal](https://github.com/evaxis/architecture/pull/5) remains
Proposed; implementation and merged earlier PRs do not approve the architecture.
The [architecture repository](https://github.com/evaxis/architecture) records
principles, decisions and [roadmap](https://github.com/evaxis/architecture/blob/main/roadmap/README.md).

## Contributing and security

Read [contribution guidance](CONTRIBUTING.md) and [security reporting](SECURITY.md).
Canonical cARL governance is under `.github/carl/`; generated harness adapters
load it. Bundled cloud/language packs are inactive, not technology decisions.

**Undecided:** implementation language, build system, execution model, backend,
cloud, detailed contracts and licensing. Public visibility does not mean
licensed open source. No Evaxis licence is selected. This bounded experiment
was explicitly authorized; further product implementation still requires its
own approval and does not inherit permission from this prototype.
Upstream cARL assets retain
their own licence in [third-party notices](THIRD_PARTY_NOTICES.md).
