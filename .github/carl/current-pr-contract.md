# PR #1: Evidence Envelope v0.1 machine-readable proposal

## Contract status

Active. The user authorized schemas, synthetic conformance fixtures,
validation-only tooling, local validation, commits, pushes and PR creation.
This PR contains a **proposal pending architectural/maintainer review**, not an
approved contract or implemented comparison behavior. Do not merge it.

## Goal and approved scope

Add modular v0.1 JSON Schemas, synthetic valid and adversarial fixture data,
machine-readable expected outcomes and minimal validation-only tooling.
Architecture owns semantics; this repository owns schema structure and fixture
data. Update relevant docs/memory, validate, commit and open a linked PR.

## Non-goals and forbidden scope

No semantic comparison engine, collection/runtime/API/storage, provider/cloud,
product language, authentication, signature verification, encryption,
cryptographic algorithm/key custody, retention, licensing, billing or
Maester-specific implementation. No CI workflow, cARL runtime/selection/
profiles/invariants/adapters, protection or unrelated repository changes.

## Plan and expected files

Follow `.github/carl/plans/pr1-evidence-envelope-v0-1.md`. Expected files:
the plan and contract; `.github/carl/memory.md`; `README.md`; the four existing
schema READMEs and versioned schema files under
`schemas/{evidence,observations,assessments,manifests}/`;
`tests/conformance/README.md`, `cases.json`, separate synthetic valid/invalid
schema fixtures; `tools/validate_conformance.py`; and `requirements-dev.txt`
only if necessary.

## Contract assertions and validation

1. Envelope, collection manifest, observation and assessment are distinct
   contracts with distinct schema/collector/rule/evaluator/comparison versions.
2. Missing, partial, failed, unsupported, stale, malformed or untrusted inputs
   remain distinct from control Pass/Fail, confirmed deletion and remediation.
3. Schema validity does not establish semantics, authenticity, freshness,
   completeness or source truth; expected comparison outcomes are machine
   readable but are not executed.
4. Every required scenario has a unique identifier, resolvable fixture,
   expected outcome and rationale; expected-invalid fixtures are handled as
   successful negative validation cases.
5. Run schema syntax/meta-validation, fixture validation/expected rejection,
   cross-reference/version/expected-result checks, documentation-link,
   whitespace and credential-pattern checks; run cARL diagnostics in both
   repositories.

## Constraints and stop conditions

Follow the scoped plan; keep all examples synthetic; do not select product
technology, provider, cryptography, licensing or retention. Stop if schema
meanings are not in the architecture proposal, if CI or product code is
required, or if conflicting edits/policy are found. Use feature branch and PR;
never merge or bypass protection.

## Carry-forward and reset

After PR creation, close this contract as submitted for review, not approved.
Preserve schema-to-architecture authority and version alignment in memory.
