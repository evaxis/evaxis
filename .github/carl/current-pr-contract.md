# PR #1: Evidence Envelope v0.1 machine-readable proposal

## Contract status

Closed — submitted for review, not approved. Targeted remediation is published
on the existing Core PR #1 branch:
https://github.com/evaxis/evaxis/pull/1. The integrity conditional tests
`claimStatus`; a complete negative envelope omits `verificationClaim` while
claiming `claims-verified`; validation confirms all other allowed statuses
remain valid without verification metadata. Producer assertions remain
distinct from receiver trust.

## Scope and invariants

Use the existing Core PR #1 branch and conformance validator. Preserve the
four-record contract and Architecture PR #3 as the human-semantic authority.
Do not redesign schemas, alter Architecture PR #3 absent a normative
inconsistency, add a test framework, implement verification/comparison, or
select product technology. Keep the existing PR open and do not merge.

## Acceptance and validation

The regression fixture must fail specifically because `verificationClaim` is
required when `claimStatus` is `claims-verified`; the valid envelope must
demonstrate a structurally valid verification claim. Validate every other
permitted integrity claim status without verification metadata. Run the full
existing schema/fixture/package/semantic-data validator, cARL diagnostics,
whitespace and credential-pattern checks, and applicable PR governance CI.
Schema validity does not establish authenticity, trust, truthfulness or
comparison correctness.

## Goal and approved scope

Revise the four v0.1 JSON Schemas and minimal validator so producer trust
statements remain claims, contradictory coverage/source-attempt combinations
and unresolved package references are rejected, and passing assessments
declare a valid basis. Add adversarial consistency cases and accurate
validation-layer documentation. Architecture owns semantics; this repository
owns schema structure and fixture data.

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

After the revision is pushed and PR checks verified, close this contract as
submitted for review, not approved. Preserve schema-to-architecture authority
and version alignment in memory.
