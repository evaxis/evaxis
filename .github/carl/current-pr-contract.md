# Portable capture final review and PR delivery

## Contract status and goal

Completed - the explicitly approved bounded remediation is implemented and
validated on all four runners at `53571d64dbf4fb61ff5180e11058c66f62b3c009`.
[Capture execution and aggregate](https://github.com/evaxis/evaxis/actions/runs/41341886934)
and [governance](https://github.com/evaxis/evaxis/actions/runs/41341886928)
passed. [PR #4](https://github.com/evaxis/evaxis/pull/4) is open against `main`;
no merge is authorized or performed. Reviewed/start head is
`321cbea0e059bc68c722efd8438d8eb75945b932` on
`goldjg-portable-capture-hardening`; fetched `main` remains
`0505243eb0cb71a2a65a3795dfef4c1104f73c64`. Preserve the completed
[hardening plan](plans/portable-capture-hardening.md).
The current plan is [final-review-delivery.md](plans/final-review-delivery.md).

Verify F1 (execution merge enforcement) and F2 (cleanup masking primary
failure), correct only confirmed gaps, execute the supported matrix and open
a reviewable PR. The new user request explicitly supersedes the historical
no-PR constraint, not the schema/trust/security limitations.

## Approved scope, files and permission checkpoint

Tier 0: repository/remote inspection and cARL/rules/check diagnostics.
Tier 1: `capture/package.py`, `tests/capture/test_capture.py`, a bounded gate
checker/regressions in `tools/ci/` and `tests/capture/`, directly related
README/docs and repository-owned memory/contract/plans.
Tier 2: focused capture workflow gate, additive required checks in existing
`main-foundations` ruleset 26000155, branch pushes/CI and PR creation/update.
The user explicitly authorized the additive ruleset/aggregate gate:
preserve all existing protections and verify failed/cancelled/skipped/missing
matrix execution cannot produce gate success. No merge is authorized.

Preserve strict up-to-date checks, GitHub Actions source binding, PR-only
updates, empty bypass actors, zero required approvals, review-thread resolution,
deletion/non-fast-forward protections and existing merge methods.
Read live state immediately before ruleset mutation; stop on concurrent
unexpected policy changes. Save prior state and verify effective read-back.
No Actions permission expansion, dependency/upstream pin/hash changes or
shared governance repair is authorized.

## Contract assertions and validation

1. Primary publication/integrity failure remains primary when staging or
   protected-handle cleanup also fails. Additional fixed safe notes are visible
   to API callers and CLI; no evidence/path values leak.
2. Cleanup-only failure is explicit, every cleanup is attempted, no uncertain
   publication reports success, no published destination is deleted, and
   no-replace/descriptor/protected-handle semantics are unchanged. Successful
   local bodies must not inherit an unrelated caller's handled exception.
3. The aggregate always runs after the four-job matrix and fails for failed,
   cancelled, skipped, neutral or missing execution; exact four fresh reports
   and mandatory-native/trust results are required.
4. Effective main rules require cARL, all four exact matrix check names and
   the aggregate from GitHub Actions. Existing no-bypass/strict/PR-only
   protections remain. Do not exercise a bypass or direct push against main.
5. Fresh Windows Server 2025/Ubuntu 24.04 x64 Python 3.11/3.13 execution passes
   all existing and new regressions, conformance, 36 PowerShell cases and
   genuine native proof; actual counts/skips/images and links are recorded.

Run focused regressions, then the isolated local Windows runner and full actual
CI matrix. Run cARL 1.0.2 diagnostics and unchanged governance. Save exact
completion evidence as a session document and provide its relative path,
final SHA, PR URL and CI links to the coordinator.

## Non-goals, trust boundaries and stop conditions

No merge/auto-merge, release, Pack publication, tenant access, Architecture
edits, Evidence Envelope/capture schema changes, attestation or receiver
redesign. Proposed specifications/ADRs remain Proposed. Receiver verification
stays `not-performed`; source truth stays `not-established`.
No crash durability, immutable storage, privileged/same-identity attacker
resistance, arbitrary filesystem certification or OS-enforced egress claim.
macOS publication remains unsupported.

Stop for unapproved scope, concurrent policy drift, unavailable required
permissions or failures requiring pin/schema/trust weakening. Organisation
ruleset enumeration returned HTTP 404 with missing `admin:org` scope;
repository effective-branch rules remain the observable enforcement source.
Record that visibility limit without expanding token scope.
The 42 existing local cARL warnings and five harness drifts remain separately
tracked, unexplained and unrepaired.

## Reconciliation and context reset

Update docs/memory for error provenance and execution gate behavior; retain
historical results as historical. Preserve shared managed assets unchanged.
Close with verified final CI/PR and actual rule read-back. Future implementation,
policy changes or merge require a new approved scope.

Effective read-back confirmed the six GitHub Actions-bound checks, strict
up-to-date/PR-only rules, no bypass actors and zero required approvals.
The full suite discovered 147 cases per runner: Windows executed 136 with
11 Linux-only skips; Linux executed 143 with four Windows-only skips. All
executed cases, conformance, 36 PowerShell cases and mandatory native proof
passed. The final delivery report records the documentation head and its own
fresh PR checks; this code-execution snapshot remains explicit historical
evidence, not authorization for future implementation or merge.
