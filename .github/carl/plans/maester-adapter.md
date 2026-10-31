# Maester adapter feasibility plan

## Plan metadata
- PR / branch: [Core PR #2](https://github.com/evaxis/evaxis/pull/2) / `feat/maester-adapter`
- Status: Closed — submitted for review; not merged
- Purpose: Establish whether actual Maester results can produce defensible Evidence Envelope v0.1 records without fabricated provenance.
- Created: 2026-10-28
- Last updated: 2026-10-31

## Scope

User-requested assessment of a replaceable Maester-to-Evaxis v0.1 import
boundary on a separate feature branch. Work only from pinned upstream source
and synthetic data; no tenant credentials, schema changes, publication or
merge.

## Purpose

Decide adapter feasibility from pinned, actual Maester output and preserve a
reproducible synthetic representation without inventing evidence provenance.

## Goal

Deliver the supported result projection and mapping documentation, validate
the fixture against actual offline output and existing Core conformance, then
submit an unmerged Core PR linked to Architecture.

## Affected files

- `docs/maester-compatibility.md`
- `tests/fixtures/maester-v3/native-result-projection.json`
- `README.md`, `.github/carl/memory.md`
- `.github/carl/current-pr-contract.md`
- `.github/carl/plans/maester-adapter.md`

## Steps

1. Compare captured native rows with a privacy-safe synthetic projection.
2. Document mapping, untrusted claims, missing provenance, unsupported
   information and deferred adversarial cases.
3. Keep schemas unchanged and omit adapter code because required source/run/
   subject/coverage information is unavailable.
4. Run Core conformance, lab checks, cARL diagnostics and whitespace/secret
   checks.
5. Commit and push this branch, then open a linked PR without merging.

## Test strategy

- Run Core `python3 tools/validate_conformance.py`.
- Run the pinned lab script and compare its nine result rows with the
  sanitized projection.
- Run cARL doctor/status/effective/trace/harness and plan checks.
- Check whitespace and added files for credential patterns.

## Risks

The fixture is a projection, not a Maester-defined export or a lossless raw
capture. No schema-valid Evaxis package or adapter output can be established
from the tested tenantless result rows.

## cARL/docs reconciliation

Core memory and docs record the durable provider-neutral trust boundary.
Close the active contract only after PR submission; do not change schemas,
invariants or dependency state.

## Assertions

1. Input is a documented, versioned representation supported by the actual
   Maester runtime.
2. The adapter rejects impossible/ambiguous inputs and records uncertainty
   rather than fabricating source evidence or verification.
3. Output, when possible, validates as a complete four-record v0.1 package and
   satisfies package consistency.
4. Test families preserve stable instance suffixes and require an
   authority/scope/native ID before any source Observation can be emitted.
5. Synthetic fixtures are not reported as tenant/provider execution.

## Steps and checks

- Read architecture semantics, four Core schemas and cARL policy.
- Inspect the pinned Maester result row implementation and exercise offline
  paths only if the pinned module/runtime is available.
- Decide adapter feasibility from exposed fields; if blocked, document the
  versioned input/mapping proposal and do not invent a runtime format.
- Run Core conformance, focused tests and cARL diagnostics; open a PR without
  merging.
