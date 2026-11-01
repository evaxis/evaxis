# Evidence preservation v0.1 implementation plan

## Status and goal

Closed - implemented and submitted for review in
[Core #3](https://github.com/evaxis/evaxis/pull/3) on
`goldjg-capture-helper-proof`, without merge.
Demonstrate synthetic source -> reusable helper -> Maester-native assessment
-> Evidence Envelope v0.1 -> schema and package-consistency validation.
Existing v0.1 and ADR 0002 remain Proposed; this is not architectural approval.

## Hydration and scope checkpoint

Read the complete 609-line assignment, canonical cARL artifacts, historical
plans, effective ten-pack `foundations` profile, current schemas, validator,
fixtures, pinned Maester lab, and Architecture v0.1 semantics. Verified current
default branch and merged PR state; the prior closed remediation contract is
superseded explicitly by the new current PR contract.

The experiment uses JSON as the portable capture representation, PowerShell
as one replaceable collector helper, Python plus existing `jsonschema` for
assembly/validation, and optional pinned Maester 3.0.0 glue. These bounded
choices do not select Evaxis's product implementation or licensing.

## Affected files

`capture/`, `integrations/powershell/`, `integrations/maester/`,
`examples/evidence-preservation/`, `tests/capture/`,
`tools/validate_conformance.py`, directly related developer/README docs,
repository-owned cARL memory, current PR contract, and this plan.
Do not modify the four existing Evidence Envelope schemas, shared governance,
Architecture, CI workflows, or the original pinned compatibility laboratory.

## Step-by-step changes

1. Define capture/0.1 data and explicit run/attempt transitions. Require
   authority/scope/native identity, source-time provenance, declared candidate
   inventory, collection limits, and precise assessment linkage.
2. Implement an explicit-session, single-writer PowerShell helper with no
   global capture state. Capture source facts at the collector boundary;
   defensively copy JSON values and preserve independent assessment records.
3. Assemble capture into one envelope, one manifest, zero-or-more observations,
   and zero-or-more assessments. Keep richer capture lineage in a namespaced
   extension; preserve all existing v0.1 coverage/reference invariants.
4. Generalize fixture-specific validation to independent multi-record
   packages. Add safe, bounded JSON handling and atomic, restricted,
   no-overwrite output; report structural consistency, never receiver trust.
5. Exercise the helper directly and from reviewed synthetic Maester-native
   tests. Bind associated results by explicit capture run identity and
   test/subject/evidence mappings, not filenames, suffixes, or timestamps.
6. Produce a real golden capture/package through the offline native example; add
   positive and adversarial executable fixtures/tests and fresh-checkout
   instructions, including supported/unsupported behavior.
7. Validate, reconcile durable docs/memory, commit, push, open a linked Core
   PR, check applicable CI, and leave it unmerged.

## Contract assertions and test strategy

1. Identity/time preservation: native IDs, source authority/scope, historical
   source timestamps, actual capture events, versions, and lineage survive
   assembly; display-only identity and invalid times fail without payload logs.
2. Lifecycle/run binding: duplicate IDs, foreign runs, outstanding attempts,
   reopened/recompleted state, mismatched sidecar associations, and wrong
   subject/reference sets are rejected directly.
3. Coverage/health: partial and unknown inventory remain representable;
   complete coverage cannot omit expected candidates; denied/unavailable
   attempts do not become assessment Fail; duplicate/overlapping sets fail.
4. Package conformance: multiple observations/assessments validate against the
   unchanged schemas; incompatible versions, references, state/outcome
   contradictions, and false receiver-verification claims are rejected.
5. Execution-associated Maester proof: pinned native synthetic tests really
   execute and their assessment records refer to previously captured source
   observations; standard native rows alone are not accepted as evidence.

Run baseline/current conformance, capture schema meta-validation, Python
unittest fixtures/assembly/adversarial tests, PowerShell parsing and helper
behavior tests, synthetic Maester execution and applicable static Pack checks,
local links/whitespace/credential-pattern checks, pinned cARL diagnostics,
and GitHub governance CI. Distinguish executed, static, skipped, and
Maester-dependent checks explicitly.

## Risks and supported boundary

One authority/scope per capture run and one envelope/manifest per package is
the initial supported cardinality. Unknown inventory uses only declared
candidates as `expectedTargets`, not an exhaustive environment inventory;
coverage remains unknown. Multiple observations for one target are allowed.
No concurrent mutation of one session, durable global run registry,
provider-connected collection, arbitrary Maester-result import, encryption,
signing, receiver verification, retention, storage immutability, or replay
policy is promised. Privileged local users and hostile ancestor-directory
replacement remain filesystem limitations.

## Reconciliation and completion checkpoint

Update developer docs and repository memory because a bounded experimental
capability and reproducible commands now exist. Do not mutate shared policy
or imply approved product/architecture decisions. Close the contract and plan
as submitted for review only after the verified PR exists; preserve remaining
limitations and separate the Architecture proposal from Core implementation.

The implementation, local validation, developer docs and durable experimental
memory are complete. The linked PR remains a review artifact, not approval of
Envelope v0.1, ADR 0002 or
[evaxis/architecture#5](https://github.com/evaxis/architecture/pull/5).
This closed plan grants no future implementation, tenant, publication, release
or merge authority; start a new approved contract for subsequent work.
