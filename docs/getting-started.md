# Getting started at the design stage

**Confirmed:** there is no product to install or deploy. This repository contains
cARL governance, proposed schemas, validation tooling and an explicitly
authorized synthetic preservation experiment. It does not select the product
stack, licence, provider contracts or architectural approval.

1. Read the [project scope](../README.md) and
   [foundation boundaries](https://github.com/evaxis/architecture/blob/main/adr/0001-foundation-boundaries.md).
2. Read `.github/copilot-instructions.md`, then hydrate the canonical
   `.github/carl/` memory, invariants, trust boundaries, tool policy and contract.
   The loader is not a separate governance authority.
3. Install cARL 1.0.2 from the
   [upstream release](https://github.com/goldjg/cARL/releases/tag/v1.0.2), using
   [documented installation instructions](https://github.com/goldjg/cARL/blob/v1.0.2/README.md).
   Verify the archive checksum for your operating system and CPU architecture.
   Do not run `carl init` over this already-initialised repository.
4. Run `carl doctor`, `carl status`, `carl pack effective`, `carl trace` and
   `carl harness status`. The active profile is `foundations`; cloud/language
   assets are bundled but inactive. No language or cloud is selected.
5. Read the [Envelope conformance instructions](../tests/conformance/README.md)
   and [reproducible preservation proof](evidence-preservation.md). The direct
   example requires no Maester; optional native execution uses exact reviewed
   lab prerequisites. Tests and output are synthetic/offline only.
6. Follow [contribution guidance](../CONTRIBUTING.md) to propose work through a
   scoped contract and PR. If using JFrog Boost, exclude `.github/carl/**`
   from optimisation as documented upstream.

**Proposed next milestone:** explicit review of the unchanged Envelope v0.1
proposal, the distinct preservation proposal, and the experimental machine
contract/helper. Existing merge state is not architectural approval. This is
not an invitation to connect a tenant, deploy infrastructure or publish a Pack.

**Undecided:** licensing, implementation stack, execution environments, storage,
identity, cryptographic details, commercial terms and integration contracts.
