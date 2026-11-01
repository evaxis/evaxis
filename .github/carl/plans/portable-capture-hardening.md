# Portable capture validation and publication hardening

## Status and goal

Completed within the approved Core-only implementation and branch-push scope.
No PR creation, merge, release or tenant access occurred.
Start from merged Core #3, commit
`0505243eb0cb71a2a65a3795dfef4c1104f73c64`.

Close concrete path-check/use substitution gaps and execute existing
credential-free capture/native integration tests on Windows and Linux.
This does not approve the proposed architecture or establish source truth,
attestation, hostile-host resistance or crash durability.

## Hydration and scope checkpoint

Read the shared loader, canonical contract/memory/invariants/trust/tool state,
historical preservation plan, and the effective ten-pack foundations profile.
All selected packs are active additive seeds at priority zero; no required
dependencies, overrides or conflicts were declared. Cloud/language/container
reference packs remain inactive. The prior contract is historical and is
explicitly superseded.

Repository inspection and remote metadata are Tier 0. Scoped code/tests/docs
and repository-owned contract/plan/memory writes are Tier 1. The user
explicitly approved Tier 2 workflow changes and branch push for CI. Do not
repair shared cARL assets, change runtime/selection/profile state, create a PR
or merge.

## Affected files and steps

1. `capture/package.py`, `tests/capture/test_capture.py`: use pinned ancestors
   and regular-file checks for reads; descriptor-relative Linux staging,
   writes, `renameat2(RENAME_NOREPLACE)` and cleanup; verified Windows
   non-reparse handles without delete sharing; private modes/ACLs before
   payload writes. Explicitly reject unsupported platforms/primitives,
   Windows streams and mapped remote drives. Add real-platform path,
   competitor, ancestor-replacement and failure regressions.
2. `.github/workflows/capture-validation.yml`, `tools/ci/`, dependency lock:
   separate safe execution CI from unchanged governance, with read-only
   contents permission, no secrets, no shared cache, pinned actions and
   verified existing prerequisites. Fetch only the reviewed native Maester
   commit and exact Graph Authentication package. No new Pester dependency.
3. Run Python conformance/capture tests, standalone PowerShell cases and the
   genuine synthetic native golden on `windows-2025` and `ubuntu-24.04`,
   x64, Python 3.11 and 3.13. Record actual PowerShell, Python, image, kernel
   and filesystem data. Required native tests cannot silently skip.
4. Push this branch and inspect actual runner results. A workflow file is not
   execution evidence. Fix coupled failures or report the precise blocker.
5. Reconcile `docs/evidence-preservation.md`, directly related README/test
   docs and repository-owned memory with measured results. Preserve shared
   managed governance and all proposal statuses unchanged.

Boundary, CI/dependency, and evidence/docs changes should be separately
reviewable commits on one branch. No stacked PRs or additional app sessions.

## Contract assertions and validation

1. Unchanged schemas, record/lineage/coverage semantics and trust outputs:
   conformance, existing mutation/positive tests and explicit receiver/source
   claim assertions run on every matrix configuration.
2. Unsafe input cannot redirect reads; non-regular descriptors are rejected
   before JSON reading and FIFO opens do not wait for a writer:
   final symlink/reparse, ancestor substitution, traversal/stream/device,
   regular-file and diagnostic negative tests execute on relevant platforms.
3. Atomic no-replace publication preserves competitors and complete files:
   actual Linux syscall and Windows rename, deterministic interleavings and
   bounded competing-process tests; assert exactly one intact winner.
4. Permissions, cleanup and failure semantics stay bounded:
   POSIX modes, Windows ACL/handle tests, parent replacement and injected
   write/fsync/rename/cleanup failures; no redirected deletion, secret output
   or success-shaped fallback.
5. Verified prerequisites drive actual native execution:
   tamper refusal before import, required zero-unexpected-skip integration,
   two observations, three assessments and Passed/Failed/Skipped associations.

Use the existing suites and credential-free synthetic data only. Preserve
file fsync but defer directory-sync/power-loss guarantees. Minimized CI
reports/logs are test artifacts, not evidence package publication.

## Risks, non-goals and escalation

macOS publication remains unsupported. Other architectures/runtimes/images,
mapped/network storage and untested filesystem configurations remain
unvalidated. No generic filesystem-trust detector is claimed.

Privileged or same-identity attackers, hostile concurrent mounts, storage
immutability, source truth, source-clock accuracy, session tamper-resistance,
upstream attestation, receiver verification and crash durability remain
limitations. Pinning/checks mitigate selected substitution races; tests do not
prove resistance to arbitrary hostile filesystems.

No provider/tenant connection, Pack publication, product release, PR creation,
merge, cryptography/authentication redesign, schema relaxation or proposal
status changes. Report Architecture dependencies instead of editing another
repository. Stop for those boundaries or unavailable required approvals.

## Reconciliation checkpoint

Update durable Core docs and repository-owned memory for actual commands,
configuration-specific validation and concrete defenses. Do not promote
historical Windows-only claims or unexecuted Linux paths into general support.
Close the contract with exact executed/unexecuted results; preserve remaining
limitations and distinguish CI, local, static and skipped evidence.

## Executed evidence and reconciliation

Implementation commit `a417d5734e59162b0a069e40b56130e25e8c865c` passed
[all four actual CI jobs](https://github.com/evaxis/evaxis/actions/runs/41337237522).
Windows Server 2025/NTFS ran Python 3.11.9 and 3.13.16 with PowerShell 7.6.7:
121 executed cases and nine Linux-only skips per job. Ubuntu 24.04 ran Python
3.11.17 and 3.13.17 with PowerShell 7.6.9: 126 executed cases and four
Windows-only skips per job. Every job discovered 130 cases, passed conformance
and 36 standalone PowerShell cases, and executed the required native golden.
Fresh native output retained exactly two observations, three assessments,
source values/timestamp strings/targets and unchanged trust-report values.

Actual Linux no-replace, ancestor/final-link replacement, FIFO and competing
publisher cases ran; Windows real handle/reparse/rename cases ran.
An initial Linux directory-descriptor failure was fixed before stream
construction and revalidated, not skipped or counted as passing.
The local isolated Windows run also passed 121 cases, conformance, 36
PowerShell cases and required native execution with nine Linux-only skips.
Developer docs preserve exact runner/image/filesystem metadata and CI links.

Docs, repository-owned memory, plan and contract are reconciled. Shared
managed governance, schemas, integrations, historical lab and Architecture
remain unchanged; no Architecture amendment is required for these bounded
implementation claims. The 42 pre-existing local cARL warnings and five drifted
harness adapters remain unexplained and unrepaired. All residual
hostile-host/attestation/session/receiver/durability limits remain explicit.
