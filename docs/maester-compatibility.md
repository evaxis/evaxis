# Maester result compatibility (research)

**Research status:** source-verified findings merged through Core
[PR #2](https://github.com/evaxis/evaxis/pull/2). This document is not an
approved integration contract.

**Evidence Envelope status:** The v0.1 specification and its Core schemas
were merged into their repositories' default branches through Architecture
PR #3 and Core PR #1. The authoritative specification nevertheless records
its status exactly as **“Proposed; pending maintainer review and explicit
architectural approval.”** The merged PRs did not change that approval status.
The four schemas remain unchanged in the preservation prototype.

**Integration status:** ADR 0002 remains Proposed. A separately authorized
experimental capture helper and synthetic native invocation wrapper now exist;
neither is an approved architectural API or a generic result importer.
See [the reproducible preservation proof](evidence-preservation.md) and the
distinct [evaxis/architecture#5](https://github.com/evaxis/architecture/pull/5)
proposal. Ordinary native rows still cannot reconstruct source observations.

The full pinned research and proposed architecture decision are available as
immutable snapshots of the merged Architecture PR #4 revision:
[compatibility research](https://github.com/evaxis/architecture/blob/b1cf74e4ae14efe123e21ac41c7667306fe71b34/research/maester-compatibility.md)
and [ADR 0002](https://github.com/evaxis/architecture/blob/b1cf74e4ae14efe123e21ac41c7667306fe71b34/adr/0002-maester-compatibility-boundary.md).
The [Architecture PR #4](https://github.com/evaxis/architecture/pull/4)
is the historical review thread, not an outstanding PR. The tracked offline verification tool is in
[`tools/maester-lab`](../tools/maester-lab/README.md); it fetches the four
pinned source commits and keeps checkouts and full runtime output outside the
Core source tree.

## What Maester 3 actually emits

The verified runtime is Maester 3.0.0 on PowerShell 7.6.0 (Maester requires
PowerShell 7.4+). The pinned source's top-level `Invoke-Maester -PassThru`
result type declares
`SchemaVersion: "2.1"` and includes `ExecutedAt`, `CurrentVersion`,
`TenantId`, `TenantContext`, optional `RunMetadata`, `Tests` and optional
attachments. Native test rows include `Id`, `Result`, `ResultDetail`,
`Duration`, `ReasonCode`, `ReasonDetail`, `ParentId`, `InstanceId`,
attributes, effective `Parameters` and a `Package` descriptor.

This row shape is a Maester result, not a source observation. The synthetic
capture projection in
[`tests/fixtures/maester-v3/native-result-projection.json`](../tests/fixtures/maester-v3/native-result-projection.json)
comes from actual offline `Invoke-MtTest -Path` output. The original, fuller
synthetic capture remains local in the ignored lab `outputs/` directory. The
projection omits free-form result/report text, nondeterministic duration and
absolute script paths; it is not an authoritative or lossless raw Maester
export. It retains Maester-generated execution reason detail.

## Mapping boundary

| Maester fact | Evaxis v0.1 interpretation |
|---|---|
| `Result` (`Passed`, `Failed`, `Investigate`) | Producer's assessment claim only. It may map to an Assessment Result only when the assessment subject, time, rule/evaluator provenance and input basis are independently explicit. |
| `Skipped`, `NotRun`, `Error`, `ReasonCode` | Execution/availability facts. A disconnected-service skip is not a security failure. Failed execution is not an assessment Fail. |
| `ResultDetail.TestResult`, markdown, error text | Untrusted, potentially sensitive explanation. Never treat as an Observation. Minimize/redact and retain only by explicit policy. |
| `Package.Id`, `Version`, `Commit` | Pack provenance; commit can be null for local development. A Pack version is not an independently declared rule version. |
| `Id`, `ParentId`, `InstanceId` | Stable Maester test/family identity. An instance suffix is not automatically a source-native identity. |
| `TenantId`, `TenantContext` | Available only in full run results; usable only when an actual authority-scoped ID exists. Do not accept display names or disconnected sentinels. |
| `ExecutedAt`, `Duration` | Run-level/result timing and elapsed duration. Neither establishes exact source collection time or per-row assessment time. |
| Pack connector, Graph connection summary, progress | Runtime/collection hints, not a complete manifest of attempts, expected inventory, permission coverage or source observations. |
| Report attachments | External report content, not an Observation. Content may carry tenant identities, details or identifiers. |

No Observation is emitted from a verdict or narrative. The v0.1 schemas
require an assessment subject with authority, scope and native ID, an
assessment timestamp, and a collection manifest with declared scope, source
attempts and coverage. Maester's normal per-test rows do not supply all those
facts. Do not invent placeholders to satisfy schema validation. If a
complete, internally consistent v0.1 package cannot be produced, reject
the import or preserve the result outside the v0.1 package boundary.

### Conservative future input contract (proposal, not implemented)

A future adapter could accept only the unmodified top-level Maester 3 result
object with `SchemaVersion == "2.1"`, plus an explicit capture record declaring
the source artifact/commit or digest, capture identity, exact execution-time
basis, test row identity, authority/scope/native target mapping, and evidence
references. These supplemental facts must be supplied by a trusted capture
boundary or explicit Pack evidence contract; the adapter must not infer them
from result text. Reject unknown schema versions, conflicting pack/test
identity, missing timestamps, ambiguous targets, disconnected sentinels, or
unsupported fields needed by v0.1. Preserve other Maester fields in the
untrusted original record, not normative evidence properties.

This is not a supported input API: the standard Maester 3 result surface does
not guarantee those capture facts. No generic result importer is implemented
because there is no defensible way to produce a complete schema-valid package
from the supported synthetic and tenantless result rows alone. The new prototype
instead captures facts while a synthetic collector still has them.

## Required negative cases and current disposition

| Case | Required handling |
|---|---|
| Pass without source payload | Keep the verdict as a producer assessment claim; emit no Observation. Reject a complete package when subject, time or input basis is absent. |
| Error during evaluation | Keep it as execution error, not an Evaxis assessment failure. |
| Skipped for disconnected service | Preserve `ServiceNotConnected` as an availability limitation, never a security failure. |
| Investigate with incomplete source data | Preserve the assessment claim and unknown/partial coverage; do not infer a failure. |
| Multiple family objects | Preserve `ParentId`/`InstanceId`; require separate authority-qualified native IDs before mapping to source subjects. |
| Same display name, different native IDs | Display name is not identity. Require distinct native IDs within the authority/scope or reject ambiguous mapping. |
| Changed rule implementation | Pack version is not a guaranteed rule version. Require explicit evaluator/rule version; otherwise preserve as unknown. |
| Unknown/conflicting test identity | Reject a conflicting ID/package relationship; retain unknown producer fields only as untrusted raw data. |
| Missing assessment/collection timestamps | Reject package mapping; never synthesize time from duration, run start, or file metadata. |
| Unknown target inventory | Leave coverage unknown; test count is not completeness. |
| Invalid/inconsistent package references | Reject through Core schema/package-consistency validation; the new capture/assembly path exercises multi-record rejection, not a generic Maester result mapper. |
| Producer says evidence is verified | Preserve only as a producer assertion; do not set receiver-established verification. |

## Verified offline paths

The tracked `tools/maester-lab/verify-maester.ps1` checks out pinned Maester
source, runs `Test-MtPack` on the demo, built-in Zero Trust Assessment, LPMS
and RK Intune Packs, then runs selected synthetic demo IDs using
`Invoke-MtTest -Path`. It disables telemetry and does not invoke
`Connect-Maester`, call Graph, install a Pack, or access a tenant.
The lab script asserts all four structural checks succeed, the nine expected
synthetic IDs/statuses are returned, the disconnected connector reports
`ServiceNotConnected`, and family parent/instance IDs are retained. By
default, the script compares selected fields from the runtime results with the
tracked Core fixture at
`tests/fixtures/maester-v3/native-result-projection.json`. The
`-SkipProjection` switch disables this comparison.

Observed result IDs/statuses:

- 1001 Passed; 1002 Failed; 1003 Investigate; 1004 skipped by its own
  configuration; 1005 Error.
- 1006 Skipped with `ServiceNotConnected` because `DEMO.Sample` was not
  connected.
- 1009 expanded into `MP.DEMO.1009.app-one`, `.app-two`, `.app-three`, with
  parent ID and instance IDs retained.

All four `Test-MtPack` checks returned `IsValid: true`. ZTA's assessed risk
was High; LPMS Medium; demo and RK Intune Low. Structural validity is not
proof that tests ran, sources were collected, or outcomes were correct.

The Graph example (1007), live tenant collection, full report attachment
execution, external module/child-process execution, connector success, and
installation/restore from GitHub were not executed. LPMS requires Graph,
Azure and Log Analytics diagnostic data/roles; RK Intune requires Graph
permissions and a populated tenant. Their result families and denial behavior
were source-inspected only.

## Original research disposition and current prototype

The original research added no adapter, schema change, new dependency, golden
Envelope or package assembly: necessary facts were absent from ordinary result
rows. Its fixture/lab remain compatibility observations, not preservation
conformance.

The new separate experiment supplies capture `0.1`, a reusable no-Maester
PowerShell helper, multi-record assembly/validation, a genuinely produced
golden package and executable positive/adversarial tests. A one-use
caller-runspace registry associates a real native callback through explicit
run/execution/invocation tokens. Native `Parameters` must match; source
observations are recorded before evaluation, never inferred from the returned
row or explanatory text.

Actual pinned execution produced one Passed, one Failed and one Skipped
result, two observations and three assessments with partial scope coverage.
The unavailable target had no fabricated source timestamp or payload.
Wrapper tokens are not upstream-issued Maester run IDs or receiver trust.
No Pack, provider collector, arbitrary result/family/error importer,
tenant connection or architectural approval is claimed.

**Next milestone:** review the distinct proposed preservation contract and Core
machine interface, including unresolved API/coverage/assessment questions,
before a separately authorized provider-connected or receiver implementation.
The [developer boundary and test evidence](evidence-preservation.md) distinguish
executed native paths, static checks and unsupported behavior.
