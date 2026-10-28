# Evidence Envelope v0.1 machine-readable proposal

## Plan metadata
- PR / branch: core PR #1 / `spec/evidence-envelope-v0.1`
- Status: Closed — submitted for review; proposal pending explicit architectural approval
- Author: Copilot
- Created: 2026-10-28
- Last updated: 2026-10-28

## Task summary

Add portable, modular JSON Schemas for the evidence envelope, observations,
assessment results and collection manifests; entirely synthetic fixtures with
machine-readable expected outcomes, including adversarial cases; and minimal
validation-only tooling. The architecture repository owns normative meaning.

## Current repository context

`schemas/{evidence,observations,assessments,manifests}/` and
`tests/conformance/` currently contain README placeholders only. Architecture
PR #2 is merged. Architecture's current proposal is the human-semantic source;
this repository owns machine-readable structures and fixture data, not a
comparison implementation.

The active cARL profile is `foundations`; only its ten selected core/CICD packs
are effective. The previous core bootstrap contract is closed history. This
plan and the new active contract authorize this scoped proposal.

## Previous contract status

The initial core foundations contract is closed and does not authorize later
implementation. The schemas and conformance test directories were explicitly
reserved for a later reviewed milestone.

## Contract lifecycle note

Schemas and fixtures are review proposals, not evidence that an evaluator,
comparison engine, authenticity service, or product exists. Preserve proposal
status until architectural approval and version alignment are recorded.

## Intentional contract amendments

The cross-PR review requests explicit producer-claim semantics, coverage and
package consistency invariants, more defensible semantic expectations, and an
assessment input basis. Revisions remain within the authorized schema and
validation-only scope; no product runtime implementation is authorized.

## Goal

Create separate versioned JSON Schema contracts for an envelope, observation,
assessment result and collection manifest, plus reproducible synthetic
conformance data and test-data consistency validation.

## Non-goals

No semantic comparison engine, cloud/API/storage/runtime, product language
selection, signature verification, encryption, crypto/key architecture,
authentication, retention policy, licensing, billing, Maester adapter or CI
workflow.

## Approved scope

- Add schemas under existing contract directories.
- Add `tests/conformance/fixtures/` records and `cases.json` expected results
  for required positive/adversarial scenarios.
- Keep schema-validity instances in `fixtures/schema-valid/` and deliberately
  invalid instances in `fixtures/schema-invalid/`, separate from semantic
  expected-result cases.
- Add a small validation-only script and a single pinned dev dependency only if
  required for JSON Schema 2020-12 validation.
- Update README/placeholders, core cARL memory/contract/plan and cross-link the
  architecture source.
- Validate schemas, fixtures, cross-references, compatibility/version
  metadata, required expected results, links, whitespace and secret patterns.
- Validate coverage target partitions, source-attempt status, package references,
  run membership and passing-assessment input basis with explicit negative cases.
- Distinguish structural fixtures, package consistency checks, compact semantic
  expectations with preconditions, and deferred behavioral implementation tests.
- Commit on a feature branch, push and open a linked review PR; do not merge.

## Forbidden scope

- Implement semantic comparison, normalization, evidence collection, runtime or
  signature/integrity verification.
- Interpret fixture expected outcomes as executed behavior.
- Include real tenant/customer identifiers, secrets, credentials or findings.
- Select product language/cloud/provider/API, storage, crypto algorithm/key
  custody, encryption, retention, licence or commercial terms.
- Modify CI workflows, cARL runtime/packs/profiles/invariants/adapters, branch
  protection or unrelated repositories.

## Trust boundaries

Treat fixture data and schemas as untrusted input. Validate structure and
cross-references explicitly. Negative fixtures are expected failures, not
validator failures. A schema-valid record is not proof of semantic validity,
authenticity, source truth, freshness or collection completeness.

## Invariants to preserve

Keep Evaxis independent of providers, runtimes and Maester. Preserve cARL and
all security invariants, avoid secrets/customer evidence, avoid unsupported
assurance claims, preserve review-only workflow and no license selection.

## Expected files / directories

- `.github/carl/current-pr-contract.md`
- `.github/carl/plans/pr1-evidence-envelope-v0-1.md`
- `.github/carl/memory.md`
- `README.md`
- `schemas/evidence/README.md`
- `schemas/evidence/envelope-v0.1.schema.json`
- `schemas/observations/README.md`
- `schemas/observations/observation-v0.1.schema.json`
- `schemas/assessments/README.md`
- `schemas/assessments/assessment-result-v0.1.schema.json`
- `schemas/manifests/README.md`
- `schemas/manifests/collection-manifest-v0.1.schema.json`
- `tests/conformance/README.md`
- `tests/conformance/cases.json`
- `tests/conformance/fixtures/schema-valid/*.json`
- `tests/conformance/fixtures/schema-invalid/*.json`
- `tools/validate_conformance.py`
- `requirements-dev.txt` only if a reproducible validator dependency is needed

## Implementation phases

1. Align record boundaries, field names, enums and version references with the
   architecture proposal.
2. Define four Draft 2020-12 schemas with explicit required fields and reject
   unknown contract fields where appropriate; keep payload/extension boundaries
   explicit.
3. Add separate synthetic valid/invalid schema instances and semantic
   expected-result cases; state comparison dimensions/outcomes and rationale as
   data.
4. Implement schema/fixture/test-data consistency checks only; do not execute
   or claim semantic comparison.
5. Validate, reconcile memory/docs and open a review PR linked to architecture.

## Acceptance criteria

1. Every schema declares its schema dialect and versioned identifier, uses
   resolvable local references, and passes meta-schema validation.
2. Valid fixtures conform to their declared schemas; negative fixtures fail the
   intended schema and are counted as expected rejection rather than suite
   failure.
3. Each required scenario has a unique ID, fixture references, machine-readable
   expected outcome and rationale; all references resolve.
4. The validator checks JSON/schema validity, cross-references, required
   version/compatibility metadata, expected-result presence, links,
   whitespace and credential patterns, but does not calculate semantic drift.
5. Synthetic fixtures cover the user-required scenarios and preserve unknown,
   incomplete, trust-error and incomparable cases without a fabricated control
   conclusion.

## Contract assertions

1. Schemas preserve distinct envelope, manifest, observation and assessment
   records, and keep source schema, collector, rule, evaluator and comparison
   model versions separate.
2. Collection status/coverage and control assessment are separate; absence,
   failure, unsupported, partial, malformed, stale and untrusted inputs cannot
   be encoded as implicit Pass/Fail or deletion.
3. Object references distinguish source authority/scope/native identity from
   display name and preserve ambiguous correlation; deletion requires positive
   lifecycle evidence.
4. Identical observations and different assessments are representable
   independently; changed observations with the same Pass remain drift-capable.
5. Validation reports schema/fixture consistency only; expected semantic
   results are documented test data, not behavior verified by a comparison
   engine.

## Test strategy

Run the local conformance validator on all schemas and fixtures. It must
meta-validate Draft 2020-12 schemas, validate fixtures by expected validity,
check unique case IDs and fixture/reference consistency, require compatibility
metadata and expected outcomes, and verify documentation links, whitespace and
secret patterns. Also run cARL diagnostics. No comparison engine exists, so
semantic expectations remain for future independent implementation testing.

## Prompt ping-pong budget

One corrective prompt is acceptable. Two require a reset and rehydration.

## Model fallback strategy

Preserve this plan, schemas' field meanings, version alignment, acceptance
status and non-goals if reset is needed. Ask before resolving ambiguous
architecture decisions.

## Stop conditions

Stop if core schemas would have to invent semantics not in the architecture
proposal, if the validator requires a product stack or CI change, if an existing
worktree/remote edit conflicts, or if any prohibited decision is required.

## Context reset requirements

After opening the PR, close this execution contract as submitted for review,
not as approval. Keep the durable core-to-architecture authority relationship
in memory. Later schema changes require a new scoped contract.
