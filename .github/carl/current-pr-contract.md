# Initial core foundations contract

## Contract status

Closed for initial file preparation: local governance, links, workflow syntax
and credential-pattern validation passed. Publication and security-setting
verification remain bootstrap operations reported separately. This historical
contract does not authorise future product implementation.

## Goal and approved scope

Prepare the future independent Evaxis core with cARL from its first commit,
documentation and explicitly unimplemented contract/scenario directories.
Tier 1 scoped file writes and Tier 2 governance/API writes are approved only for
the three named Evaxis repositories. No harness authority changes are approved.

## Plan and expected files

1. Inspect existing state; initialise cARL and activate the foundations profile.
2. Populate `.github/carl/memory.md` with independence and assurance invariants.
3. Add `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODEOWNERS`,
   `THIRD_PARTY_NOTICES.md`, `docs/getting-started.md`, README-only placeholders
   under `schemas/`, `examples/`, `tests/conformance/`, and governance CI.
4. Validate locally, make the first commit, push to empty `main`.
5. Apply supported security settings and verify remote state.

## Non-goals and forbidden scope

No evidence processing, storage, drift logic, authentication, billing, hosting,
fictional schemas/findings/tests, stack/cloud/backend choice, licensing terms,
paid resources, releases, other projects, replacement logo or invented HTML.
No force pushes, deletion, bypassed reviews, auto-merge, weakened protections,
workflow administration tokens or committed secrets.

## Architectural and security constraints

Preserve `memory.md` invariants and trust boundaries, plus bundled policy.
Maester remains a proposed integration, never the core's execution/storage
foundation. Keep managed cARL files canonical and local policy in memory.
No public visibility claim implies open-source licensing.

## Contract assertions and validation

1. The remote initial commit includes cARL and all required documentation:
   inspect history and Git tree.
2. `carl doctor`, `status`, `pack effective`, `trace`, `harness status` pass;
   only core governance and CI/CD packs are effective.
3. All planned directories are labelled unimplemented; no product code,
   schemas, customer data or provider contracts exist.
4. Local links, remote links and the canonical avatar resolve.
5. Staged whitespace/credential checks and real cARL CI pass; read back GitHub
   security/protection settings and report limitations rather than fake success.

## Risks, stop conditions and escalation

Stop the affected operation on unexpected existing content, permissions failure
or policy conflicts. Escalate reserved technical/commercial decisions.
Avoid sole-maintainer lockout: require PRs but not impossible self-approval.
Never grant automation a bypass or weaken settings to make checks succeed.

## Carry-forward and context reset

Only stable memory/invariants carry forward. Subsequent changes require feature
branches and PRs. Close this bootstrap contract after local preparation and
validation; replace it with explicit approved scope before new work.
