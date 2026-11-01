# Portable capture validation and publication hardening

## Contract status

Active - explicitly approved for Core-only implementation and branch push
for actual Windows/Linux CI execution. No PR creation or merge is authorized.
This supersedes the closed preservation experiment, now merged in
[Core #3](https://github.com/evaxis/evaxis/pull/3). Verified starting `main` is
`0505243eb0cb71a2a65a3795dfef4c1104f73c64`.

## Goal and approved scope

Harden concrete capture/publication filesystem boundaries and execute the
existing credential-free suites on Windows and Linux. The linked plan is
[portable-capture-hardening.md](plans/portable-capture-hardening.md).

Approved scope includes pinned/descriptor-relative filesystem I/O, regular-file
and unsupported-path checks, private staging, atomic no-replace publication,
safe cleanup, concrete regressions, a separate least-privilege test workflow,
integrity-checked existing validation/native prerequisites, actual runner
execution, developer docs and repository-owned cARL reconciliation.
CI targets x64 `windows-2025` and `ubuntu-24.04`, Python 3.11 and 3.13,
with actual runner-provided PowerShell recorded. Passing configurations are
bounded execution evidence, not universal platform/security support.

## Non-goals and forbidden scope

No changes to existing Envelope/capture schema invariants, Architecture,
shared cARL policy/invariants/templates/packs/adapters/runtime/selection/profiles,
the existing governance workflow, the historical compatibility lab, or
unrelated repositories. No tenant connection, credentials, real evidence,
automatic evidence upload, Pack publication, release, PR creation, merge,
comparison engine, receiver-verification redesign or cryptographic assurance.

Evidence Envelope v0.1, ADR 0002, Evidence Preservation v0.1 and ADR 0003
remain Proposed. Receiver verification stays `not-performed`.
Session tamper-resistance, upstream attestation, crash-durability guarantees
and general hostile-filesystem/production-suitability claims are non-goals.
Report any Architecture dependency to the coordinator instead of editing it.

## Expected files

- `.github/carl/current-pr-contract.md`
- `.github/carl/plans/portable-capture-hardening.md`
- `.github/carl/memory.md`
- `capture/package.py`
- `tests/capture/test_capture.py`
- `tests/capture/README.md`
- `.github/workflows/capture-validation.yml`
- `tools/ci/`
- Python validation dependency lock
- `docs/evidence-preservation.md`
- `README.md`

PowerShell export changes require a concrete coupled boundary failure.

## Contract assertions and validation

1. Existing schemas, lineage, coverage, source identity/time semantics and
   receiver/source-truth report values remain unchanged.
2. Unsafe input paths/files cannot redirect reads or block on FIFOs/devices;
   no-follow and ancestor-substitution regressions execute per platform.
3. Actual Linux `renameat2(RENAME_NOREPLACE)` and Windows rename preserve
   competitor destinations and expose complete bundles only.
4. Private permissions, pinned cleanup and explicit failure semantics survive
   selected parent replacement and write/fsync/rename/cleanup failures.
5. Every CI configuration executes existing conformance/Python/PowerShell
   suites and the genuine two-observation/three-assessment native golden with
   verified prerequisites and no unexpected native skip.

Validate locally on Windows and on actual authorized CI runners. Record
commands, runtime/image/filesystem metadata, skips, results and CI links.
A workflow file or platform-mocked test is not platform execution evidence.

## Trust boundaries and stop conditions

All payloads, paths and native results remain untrusted. Keep existing size,
depth, credential, diagnostic, identity and schema checks. Operate only in
caller-approved local storage; pinned ancestors mitigate selected replacement
races, not privileged/same-identity attackers or hostile filesystems generally.
Local digests/association tokens establish neither publisher/source identity
nor receiver trust. No operating-system-enforced egress isolation is claimed.

Read-only inspection is Tier 0. Bounded code/tests/docs and repository-owned
contract/plan/memory writes are Tier 1. The user explicitly approved Tier 2
new CI workflow/dependency preparation and this branch's push for CI.
Never force-push, create a PR or merge. Reuse existing Python and exact native
Maester/Graph prerequisites, installed only in isolated session/runner storage.
Manifest changes or actual missing-dependency failures precede installation.

Stop for tenant/credential requirements, schema/semantic weakening, new product
dependencies, unapproved scope, unavailable permissions/runners or required
Architecture amendments. Do not repair the unexplained historical cARL
warnings or weaken gates to make execution succeed.

## Reconciliation

Update docs and repository-owned memory for concrete defenses, commands and
measured platform-specific results. Preserve shared managed governance
byte-for-byte. Close with persistent commit state and exact executed/unexecuted
evidence, not PR submission or approval of architecture.

## Context reset

This contract does not authorize subsequent providers, policies, publishing,
release, receiver trust or merge. Future work requires a new approved contract.
macOS publication stays unsupported; untested configurations and all remaining
trust/hostile-host/durability limitations must remain explicit.
