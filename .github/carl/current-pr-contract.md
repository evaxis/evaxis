# Maester compatibility review remediation

## Contract status

Active — user-authorized remediation of findings F1–F3 in
[Core PR #2](https://github.com/evaxis/evaxis/pull/2), on `feat/maester-adapter`.
The existing PR remains open and unmerged. Evidence Envelope v0.1 artifacts
are merged to their default branches, while the authoritative semantic
specification remains explicitly proposed pending architectural approval.

## Goal and approved scope

Correct status language and cross-repository links in Core's compatibility
documentation, and add narrowly scoped, tracked offline verification tooling
that fetches only the four specified immutable upstream commits, runs reviewed
synthetic-only tests, asserts disconnected/family behavior, and optionally
compares the sanitized projection. Keep full raw output local. Update this
contract, plan and Core memory for this reproducibility boundary.

## Non-goals and forbidden scope

No adapter, provider-specific schema/type, change to v0.1 schemas or
conformance semantics, credentials, Microsoft Graph, production tenant,
Pack installation/publication, arbitrary upstream/latest code execution,
vendoring, full raw-output publication, merge, or unrelated tooling rewrite.
Do not claim provider-connected compatibility or source capture completeness.

## Expected files

- `.github/carl/current-pr-contract.md`
- `.github/carl/memory.md`
- `.github/carl/plans/maester-adapter.md`
- `docs/maester-compatibility.md`
- `tests/fixtures/maester-v3/native-result-projection.json`
- `tools/maester-lab/verify-maester.ps1`
- `tools/maester-lab/README.md`

## Contract assertions and validation

1. State v0.1's exact merged-but-proposed status and keep future ADR/adapter/
   capture interfaces explicitly proposed or unimplemented.
2. Replace feature-branch architecture links with PR #4 permalinks that resolve
   before and after the target files merge.
3. From a fresh checkout, the tool checks exact pinned commits and runtime
   prerequisites; no automatic dependency install, tenant/Graph connection,
   or telemetry is used; only listed synthetic test IDs execute.
4. Assert expected nine row outcomes, disconnected reason and family identity;
   compare only the sanitized projection when supplied; never emit Evaxis
   records or treat the fixture as an executable adapter test.
5. Keep raw results in a local untracked workspace, and leave all four v0.1
   schemas and existing fixtures unchanged.

Run the tracked offline tool in the pinned local environment, Core conformance,
JSON/Markdown/link, whitespace/secret scans, cARL diagnostics and applicable
GitHub CI. Report source inspection, static checks, runtime execution and
provider-connected capability separately; do not claim adapter conformance.

## Trust boundaries and stop conditions

Only exact pinned source commits and reviewed offline-safe demo IDs may execute.
Do not accept credentials, connect Graph/Maester, install Packs, or write raw
output under tracked product paths. Stop if a pin mismatch, runtime mismatch,
unexpected synthetic row/status, missing dependency, or unexpected external
connection requirement occurs; report instead of silently installing or
falling back.

## Reconciliation

Update Core docs and memory for the tracked, offline-only reproducibility
boundary. Keep Maester optional and outside provider-neutral schemas.
