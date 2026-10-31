# Maester compatibility review remediation plan

## Plan metadata
- PR / branch: [Core PR #2](https://github.com/evaxis/evaxis/pull/2) / `feat/maester-adapter`
- Status: Active — F1–F3 review remediation; existing PR remains open and unmerged
- Purpose: Correct status/links and check in a pinned, offline-only reproduction tool without implementing an adapter.
- Created: 2026-10-28
- Last updated: 2026-11-02

## Scope

Remediate Core PR findings F1–F3 on the existing branch. v0.1 artifacts are
merged into default branches but the semantic specification remains proposed
pending explicit architectural approval. Work only from exact pinned sources
and reviewed synthetic data; no tenant credentials, schema changes, Pack
publication, adapter implementation or merge.

## Goal

Fix the status description; use PR #4 permalinks for pending Architecture
documents; add tracked instructions and a PowerShell tool to fetch exact
commits, run only reviewed offline synthetic tests, validate expected row
statuses/family identity/disconnected behavior, and optionally compare the
existing privacy-safe projection.

## Affected files

- `docs/maester-compatibility.md`
- `tools/maester-lab/verify-maester.ps1`
- `tools/maester-lab/README.md`
- `.github/carl/memory.md`
- `.github/carl/current-pr-contract.md`
- `.github/carl/plans/maester-adapter.md`

## Tool requirements

- Fetch only the four immutable SHA pins; verify each resulting `HEAD`.
- Require PowerShell 7.4+ and Maester 3.0.0; never install modules or Packs.
- Operate only on synthetic demo test IDs 1001–1006 and 1009; do not call
  Graph, `Connect-Maester`, `Install-MtPack`, or publish.
- Disable telemetry, store full runtime output only in a local untracked
  workspace, and print only minimized identifiers/status fields.
- Fail closed on missing dependencies, pin/runtime mismatch, or unexpected
  rows. Projection comparison is optional and compares only listed fields.

## Assertions and validation

1. Exact upstream commit, PowerShell and Maester versions are checked.
2. Four Pack structures statically validate; nine synthetic rows have expected
   statuses; disconnected service is `ServiceNotConnected`.
3. Three family rows preserve `ParentId`/`InstanceId`; optional Core projection
   comparison matches only its selected fields.
4. No automatic install, tenant/Graph call, full-output publication, schema
   change, Evaxis output, or claim of adapter conformance occurs.
5. Core conformance, JSON/Markdown/link checks, secret scan, hygiene, cARL
   diagnostics and applicable CI pass; report any unavailable check.

## Stop conditions

Stop on mismatched SHA or runtime, unexpected network/credential dependency,
failed structural/synthetic assertions, or any request to infer provenance,
change v0.1 schemas, publish a Pack, or implement an adapter.
