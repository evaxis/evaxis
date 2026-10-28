<!-- version: 1.1.0 -->
# PR #1 integrity claim conditional remediation

## Plan metadata
- PR / branch: Core PR #1 / `spec/evidence-envelope-v0.1`
- Status: Active targeted remediation
- Author: Copilot
- Created: 2026-10-28
- Last updated: 2026-10-28

## Task summary

Correct the integrity schema's `claims-verified` conditional, which currently
tests the obsolete `status` property instead of `claimStatus`. Add a negative
whole-envelope fixture and validator assertions for this and all other allowed
claim statuses.

## Current repository context

Core PR #1 is open on its existing feature branch. Its four schemas and
validation-only conformance tool are proposals; Architecture PR #3 owns
normative semantics. The worktree was clean and synchronized with the remote
PR head before this task.

## Previous contract status

The previous Core PR #1 contract was closed as submitted for review, not
approved. This narrowly scoped remediation supersedes that execution scope
without changing the proposed product or architectural decisions.

## Contract lifecycle note

The PR remains open for review. Closing this task contract means submitted for
review, not approved or merged.

## Intentional contract amendments

None. This corrects the schema conditional to match the existing `claimStatus`
property and existing producer-assertion semantics.

## Goal

Reject an integrity object that claims `claims-verified` but omits
`verificationClaim`, while preserving permitted other claim statuses without
verification metadata.

## Non-goals

No receiver verification, signature checking, trust service, semantic
comparison, schema redesign, Architecture PR #3 edit, test framework,
implementation-language, provider, or cryptographic choice.

## Approved scope

- Correct the `if` property in `schemas/evidence/envelope-v0.1.schema.json`.
- Add a complete synthetic negative envelope under
  `tests/conformance/fixtures/schema-invalid/`.
- Extend existing validator and conformance documentation to check the
  conditional and allowed status behavior.
- Run existing validation and cARL/GitHub governance checks.
- Commit and push to the existing Core PR #1 branch; update the PR description.

## Forbidden scope

Do not change Architecture PR #3 absent a demonstrated normative
inconsistency. Do not merge either PR, change unrelated conditionals without
direct evidence and regression tests, or imply that claims establish actual
verification or trust.

## Trust boundaries

The schema validates producer-supplied claim structure only. It cannot
establish that a verifier exists, performed the stated method, authenticated
the producer, or established authenticity, freshness, source truth or
completeness.

## Invariants to preserve

- `claimStatus` values remain producer-assertion vocabulary.
- A `claims-verified` claim requires structurally valid `verificationClaim`.
- Other permitted statuses do not acquire an accidental metadata requirement.
- Architecture PR #3 remains the normative semantics authority.
- No production verification or comparison behavior is implemented.

## Expected files / directories

- `.github/carl/current-pr-contract.md`
- `.github/carl/plans/pr1-integrity-claim-conditional.md`
- `schemas/evidence/envelope-v0.1.schema.json`
- `tests/conformance/fixtures/schema-invalid/claims-verified-without-verification-claim.json`
- `tests/conformance/README.md`
- `tools/validate_conformance.py`

## Implementation phases

1. Reproduce the defect at the fetched PR head and inspect peer conditionals.
2. Fix the property name and add targeted positive/negative checks.
3. Run validation, inspect diff, commit and push to the existing branch.
4. Update PR description and verify governance CI.

## Acceptance criteria

1. A complete otherwise-valid envelope with `claims-verified` and no
   `verificationClaim` is rejected specifically for missing that property.
2. A valid `claims-verified` claim with structurally valid metadata passes.
3. Each other permitted `claimStatus` passes without `verificationClaim`.
4. All existing schema, fixture, package-consistency and 22 semantic
   expectation-data checks pass.
5. cARL diagnostics, whitespace/credential checks and PR governance checks
   pass; no trust or comparison guarantee is claimed.

## Contract assertions

1. Validate the negative whole-envelope regression fixture against the
   envelope schema and require the `verificationClaim` required-property error.
2. Validate the existing positive envelope and assert it contains a valid
   producer verification claim.
3. Validate each other `claimStatus` against the integrity schema without a
   verification claim.
4. Run the complete existing validator and governance checks.

## Test strategy

The current validator's fixture loop must reject the new invalid fixture for
the intended `required` violation. Its integrity-specific checks verify the
existing positive envelope and enumerate all permitted statuses to ensure only
`claims-verified` requires claim metadata. The complete validation run also
covers schema meta-validation, positive/negative fixtures, linked-package
consistency and semantic expectation-data integrity. No behavioral evidence
comparison or cryptographic trust is tested.

## Prompt ping-pong budget

One corrective prompt is acceptable. Two require reset and rehydration.

## Model fallback strategy

Preserve this targeted scope, no-merge boundary and claim-versus-trust
distinction if a context reset is needed.

## Stop conditions

Stop if the branch or worktree has conflicting changes, if the schema does not
reproduce the identified defect, or if normative architecture changes are
required. Report unrelated conditional observations instead of expanding
scope.

## Context reset requirements

After pushing and verifying the existing PR, close this contract as submitted
for review, not approved. Leave both PRs open and unmerged.
