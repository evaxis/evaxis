# Maester result import boundary

## Contract status

Closed — submitted for review in
[Core PR #2](https://github.com/evaxis/evaxis/pull/2), unmerged. Research and
adapter-feasibility work is complete on `feat/maester-adapter`, based on the
merged v0.1 baseline. The v0.1 schemas remain unchanged and architecture-owned
semantics govern interpretation.

## Goal and approved scope

Determine whether Maester's actual result rows can be mapped to the four
Evidence Envelope v0.1 record types without inventing evidence. Preserve
source-derived synthetic rows and a precise mapping specification. Implement
an adapter only if real source/runtime behavior supports a defensible,
schema-valid package; otherwise document the unsupported cases and blocker.

## Non-goals and forbidden scope

No product service, provider dependency in Core contracts, tenant access,
credentials, Pack publication, public schema modification, trust verification,
source observation inferred from test verdict/text, production claims, or
unsupported runtime surface. Do not copy upstream implementation or merge.

## Expected files

- `.github/carl/current-pr-contract.md`
- `.github/carl/memory.md`
- `.github/carl/plans/maester-adapter.md`
- `README.md`
- `docs/maester-compatibility.md`
- `tests/fixtures/maester-v3/native-result-projection.json`
- Adapter implementation and output tests only if the supported runtime
  provides sufficient provenance.

## Contract assertions and validation

1. Keep Maester execution status, verdict, Evaxis assessment outcome, evidence
   availability, collection health, coverage and trust distinct.
2. Never create Observations from a verdict or narrative, and never turn
   inaccessible/skipped collection into a security failure.
3. Preserve family row identity without promoting it to provider-native
   identity; reject missing/ambiguous subject or timestamp provenance.
4. Keep unknown producer fields and verification assertions untrusted; do not
   claim receiver verification or environmental completeness.
5. Validate the existing conformance suite and the privacy-safe projection
   against actual offline output; label synthetic evidence honestly.

Run the Core conformance validator and pinned offline lab assertions, compare
the fixture projection with runtime rows, and perform whitespace,
secret-pattern and cARL checks. The adapter was found premature, so no adapter
tests or schema-valid generated package are claimed. No public schema change
or new dependency is authorized by this contract.

## Trust boundaries and stop conditions

Do not install or execute unreviewed Pack scripts with tenant credentials.
Upstream sources, helper modules, result text and report attachments are
untrusted. Stop adapter coding if runtime output is inaccessible or required
fields cannot be derived without fabrication; deliver a mapping specification
and explicit blocker instead. Feature branch and PR only.

## Reconciliation

Update durable Core documentation/memory only for confirmed reusable findings;
do not make Maester foundational to Core. Close this contract as submitted for
review, not merged or approved.
