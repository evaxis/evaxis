# Experimental Evidence Preservation v0.1

**Implemented experiment, not an approved product contract.** Capture contract
`0.1` is separate from the unchanged Evidence Envelope `0.1` schemas. The
[Envelope specification](https://github.com/evaxis/architecture/blob/main/specifications/evidence-envelope-v0.1.md)
remains **Proposed; pending maintainer review and explicit architectural
approval**. The distinct preservation proposal is in
[evaxis/architecture#5](https://github.com/evaxis/architecture/pull/5).
Neither this prototype nor merged earlier PRs approves that architecture,
selects a product stack or licence, or authorizes tenant-connected testing.

## Reproduce without Maester

Use Windows, PowerShell 7.4+, Python 3.11+, and the existing
`jsonschema==4.26.0` validation dependency in `requirements-dev.txt`.
The verified environment was PowerShell 7.6.9 and Python 3.13.16.
No Maester or Microsoft Graph module is required for this path.

From the repository root, set `$python` to your existing trusted Python
executable, or prepare an approved environment if the dependency is not already
available. For example, keep it outside the checkout:

```powershell
$venv = Join-Path $env:TEMP ('evaxis-validation-' + [Guid]::NewGuid())
python -m venv $venv
$python = Join-Path $venv 'Scripts\python.exe'
& $python -m pip install -r requirements-dev.txt
$env:PYTHONDONTWRITEBYTECODE = '1'
```

Prerequisite installation can use the network; evidence execution does not.
The scripts never install dependencies, authenticate, or upload evidence.
The caller chooses a trusted Python executable and a **new** output directory
whose parent already exists:

```powershell
$output = Join-Path $env:TEMP ('evaxis-offline-' + [Guid]::NewGuid())
pwsh -NoProfile -File examples\evidence-preservation\Invoke-OfflineExample.ps1 `
  -OutputDirectory $output -PythonCommand $python
& $python capture\package.py validate-capture --input (Join-Path $output 'capture.json')
& $python capture\package.py validate-package --input (Join-Path $output 'package.json')
```

Expected output is a completed capture and a validated package with **two
observations and three assessments**. One setting passes, one fails, and the
unavailable third target has no observation and an unknown, not-run assessment.
The declared three-target scope has partial collection and partial coverage.
These are explicitly synthetic facts, not provider findings.

To retain a genuinely unknown inventory, use another new destination:

```powershell
$unknown = Join-Path $env:TEMP ('evaxis-unknown-' + [Guid]::NewGuid())
pwsh -NoProfile -File examples\evidence-preservation\Invoke-OfflineExample.ps1 `
  -InventoryStatus unknown -OutputDirectory $unknown -PythonCommand $python
```

Only declared candidates are retained as `expectedTargets`; they are not an
exhaustive environment inventory. Coverage remains `unknown` even though the
example accounts for those candidates.

## Components and portable data

| Component | Responsibility |
|---|---|
| [`capture-v0.1.schema.json`](../capture/contracts/capture-v0.1.schema.json) | Separate provider-neutral capture data contract; references, rather than replaces, the four v0.1 record schemas. |
| [`Evaxis.Capture.psd1`](../integrations/powershell/Evaxis.Capture.psd1) and module | One replaceable author-facing PowerShell implementation with explicit session ownership. |
| [`capture/package.py`](../capture/package.py) | Capture validation, assembly, schema/package/lineage checks, and atomic local publication. |
| [`SyntheticCollector.ps1`](../examples/evidence-preservation/SyntheticCollector.ps1) | Reviewed credential-free collector/rule example used both directly and inside a real native callback. |
| [`integrations/maester/`](../integrations/maester/README.md) | Optional pinned-engine invocation association; no Maester dependency in the reusable helper or Core schemas. |
| [`golden/`](../examples/evidence-preservation/golden/README.md) | Genuinely generated complete capture/package, not verdict-to-observation reconstruction. |
| [`tests/capture/`](../tests/capture/README.md) | Positive, adversarial, lifecycle, assembly, privacy, filesystem, CLI, and native integration tests. |

The capture carries run and collector identity, source authority/scope,
configuration version when available, requested scope, declared inventory,
attempts, independent observations, explicit non-observations, and assessments.
Observation records include native target identity, object kind, defensible
lifecycle basis, source time, source representation/reference, and schema
identity/version. Assessment records retain subject, independent rule/evaluator
versions, assessment time, precise observation references, execution state,
conclusion, input basis and control coverage.

One run has **one authority/scope**. Target identity is the case-sensitive tuple
`(authority, scopeId, nativeId)`, never display name. Multiple observations may
describe one target. One package has **one envelope, one manifest, zero-or-more
observations, and zero-or-more assessments**. An explicitly empty known scope
can contain no observations; an unsuccessful or assessment-only collection
must not invent any.

The package transport wrapper has exactly `envelope`, `manifest`,
`observations`, and `assessments`. Its inner records use the existing schemas.
The reserved `evaxis.capture/0.1` extension retains richer inventory, attempt
IDs, clock origins, capture events, transformations and optional framework
associations. Envelope and record lineage must agree, including the manifest's
attempt, coverage and visibility-constraint projection. A caller cannot supply
that reserved namespace inside capture records and have it silently overwritten.
This experimental extension does not introduce new normative Envelope fields.

## PowerShell author API and lifecycle

Import the manifest, not Maester:

```powershell
Import-Module .\integrations\powershell\Evaxis.Capture.psd1
```

| Operation | Required context and behavior |
|---|---|
| `New-EvaxisCaptureSession` | `Collector`, `Source`, `RequestedScope`, `ExpectedTargets`, `InventoryStatus`, `InventoryBasis`; starts an owned `collecting` session with an actual UTC event. Optional `CollectionRunId`, caller-owned `RunRegistry`, `CollectorConfiguration`, and `FrameworkContext`. |
| `Start-EvaxisSourceAttempt` | `Session`, unique `AttemptId`, `IntendedTargets`; source/scope inherited from the run, targets must be declared, state becomes `in-progress`. |
| `Add-EvaxisObservation` | `Session`, active `AttemptId`, unique `ObservationId`, `Target`, `ObservedAt`, `TimestampOrigin`, `ClockBasis`, `ObservationType`, `ObservationSchema`, `Representation`; optional `CollectionRunId` must match and optional `Transformations` are retained. |
| `Complete-EvaxisSourceAttempt` | `Session`, `AttemptId`, `Status`; non-success requires a minimized `Limitation` with `code` and `description`. Optional `VisibilityConstraints`. Records actual completion; successful attempts must observe every intended target. |
| `Add-EvaxisNotObservedTarget` | `Session`, completed non-success `AttemptId`, `Target`, matching `Reason`; records absence and its actual recording event, never an observation or deletion inference. |
| `Add-EvaxisAssessment` | `Session`, unique `AssessmentId`, `Subject`, versioned `Rule` and `Evaluator`, `AssessedAt`, `TimestampOrigin`, `ClockBasis`, `ExecutionStatus`, `Outcome`, `ObservationReferences`, `InputBasis`, `ControlCoverage`; optional opaque `FrameworkAssociation`. |
| `Complete-EvaxisCapture` | `Session`, `CollectionStatus`, `CoverageStatus`; requires finished attempts and consistent target accounting, records actual completion, then sets `completed`. |
| `Get-EvaxisCaptureDocument` | Returns a defensive JSON snapshot of a completed `Session`; no PowerShell/runtime state is serialized. |
| `Export-EvaxisCapture` | Completed `Session`, explicit new `OutputDirectory`, optional trusted `PythonCommand`; full validation precedes persistence and success reporting. |

Collector, rule and evaluator identities use explicit `authority`, `id` and
`version`. Collector identity additionally requires `identityClaimStatus`,
which remains a producer claim. Source and scope require `authority` and
`scopeId`. Targets require `nativeId`; observed targets also require `kind`
and lifecycle `state`/`basis`. Unknown lifecycle is valid. Confirmed deletion
requires positive source-attributable lifecycle evidence, not non-observation.
Representations require exactly one `content` or `reference` and an explicit
encoding. JSON null is a value, not proof of source unavailability.

The executable example supplies complete author arguments:

```powershell
. .\examples\evidence-preservation\SyntheticCollector.ps1
$run = New-EvaxisSyntheticRun
foreach ($object in $run.Fixture.objects) {
  Invoke-EvaxisSyntheticObject -Session $run.Session -Fixture $run.Fixture `
    -NativeId $object.target.nativeId `
    -Evaluator @{ authority = 'urn:evaxis:synthetic-evaluator'; id = 'offline-rule'; version = '0.1.0' } |
    Out-Null
}
Complete-EvaxisCapture -Session $run.Session -CollectionStatus partial -CoverageStatus partial
$destination = Join-Path $env:TEMP ('evaxis-author-' + [Guid]::NewGuid())
Export-EvaxisCapture -Session $run.Session -OutputDirectory $destination -PythonCommand $python
```

Run transitions are `collecting -> completed`, exactly once. Attempt transitions
are `in-progress -> succeeded|failed|unsupported|unavailable|denied|malformed|not-attempted`,
exactly once. Completed state cannot reopen; duplicate attempts/records, foreign
runs, unresolved references and contradictory coverage/status fail explicitly.
No implicit retry or idempotent completion is implemented.

Treat `Session.Document` as read-only in process. The example reads its
previously captured observation before evaluating the boolean; public operations
own mutation. Do not dump, serialize or pass the session through framework
parameters. The session is a producer-side handle, not an immutable or
tamper-proof security boundary.

One session is single-writer and bound to its creating runspace. Sharing it
across runspaces is rejected; independent sessions may have independent owners.
Optional `RunRegistry` is a caller-owned `HashSet[string]` detecting duplicate
collector-authority/run-ID pairs in that registry. It is not durable global
deduplication, is not automatically synchronized, and does not establish replay
protection. IDs default to new GUIDs; reuse in another registry/destination is
not globally detected.

The helper checks primary types, identity, time, state, evidence linkage and
coverage at the author boundary. Full authoritative record-schema validation
and package/lineage validation occur before export. It does not duplicate the
entire JSON Schema implementation in PowerShell.

## Clocks, values and assessment basis

Caller-supplied `observedAt` stays a string with its original offset/spelling and
required origin/clock assumptions. The fixture deliberately uses historical
times, including `Z` and `+00:00`; neither is replaced by run start, file time,
capture time, native result time or duration. Synthetic JSON decoding avoids
PowerShell's automatic ISO-string-to-`DateTime` conversion.

Run/attempt/capture/recording events use actual local UTC. The native evaluator
records its own actual event, separate from source time. Imported assessment
times must be explicit and not later than their recording event; clock skew
is not silently corrected. Fractional timestamp digits are preserved and
interval comparisons retain sub-microsecond precision. Clock accuracy,
synchronization and freshness remain unverified. Leap-second timestamps are
unsupported and fail rather than being normalized.

Representations are defensively copied, including case-sensitive object keys,
array cardinality, scalar types, explicit null and caller-supplied units.
The example's decoder supports exact signed 64-bit integer literals and JSON
primitives. The broader portable decoder rejects non-finite numbers and decimal
tokens that cannot round-trip without numeric value loss through this
implementation. It does not silently approximate high-precision values.
Logical JSON values are preserved; original artifact byte formatting is not.
Transformation annotations may be retained with model/version and input/output
references; no transformation engine, equivalence proof or digest computation
is implemented.

A rule failure means a completed evaluation concluded `fail`; it is not
collection failure. Failed/unsupported/not-run execution cannot conclude
`pass` or `fail`. No-input cannot produce a verdict. Legitimate declared-scope
or external-reference bases remain supported by v0.1, but must be explicit,
with consistent control coverage. Assessment-only input never manufactures
source observations. Validation does not independently prove a rule's truth.

## Optional, actual Maester-native proof

Use the reviewed lab's immutable Maester source commit
`b8ad89557a831d3d3d7c369174300701243af8a6`, declaring Maester 3.0.0, and its exact
`Microsoft.Graph.Authentication` 2.27.0 prerequisite. The prerequisite is loaded
as a dependency only. No connection is made; a connected Graph context is
explicitly refused, telemetry is disabled, and no tenant test is authorized.

Prepare the prerequisite in an approved module location if missing; neither
proof script installs it. A user-local example is:

```powershell
$modules = Join-Path $env:TEMP ('evaxis-modules-' + [Guid]::NewGuid())
New-Item -ItemType Directory -Path $modules -ErrorAction Stop | Out-Null
Save-Module -Name Microsoft.Graph.Authentication -RequiredVersion 2.27.0 -Path $modules
$env:PSModulePath = $modules + [IO.Path]::PathSeparator + $env:PSModulePath
$lab = Join-Path $env:TEMP ('evaxis-maester-lab-' + [Guid]::NewGuid())
pwsh -NoProfile -File tools\maester-lab\verify-maester.ps1 -WorkspacePath $lab
$maester = Join-Path $lab 'refs\maester'
$native = Join-Path $env:TEMP ('evaxis-native-' + [Guid]::NewGuid())
pwsh -NoProfile -File integrations\maester\Invoke-SyntheticMaester.ps1 `
  -MaesterSourcePath $maester -OutputDirectory $native -PythonCommand $python
```

The lab fetch phase uses HTTPS for exact public source commits. After
prerequisites are available, the new proof is synthetic/offline. It refuses
a dirty or mismatched source checkout; it never installs or publishes a Pack.
The custom example is a native test plus required neighboring Markdown, **not
a Pack**.

The pinned parser permits only function definitions at a custom test file's
top level and scalar/string-array configuration, not session objects. The
optional module therefore holds a narrowly scoped one-use registry in the
caller runspace, only around the actual invocation. Native parameters are
`CollectionRunId`, `ExecutionId`, and `InvocationId`; returned native
`Parameters` must contain those exact explicit values. The callback consumes
that registered context, captures the source fact, evaluates the captured
value, records the assessment, and then returns the normal native result.

The wrapper checks one result and one associated assessment per invocation,
test identity, target, actual native result, execution/conclusion mapping, and
parameter/run association before completion/export. Registry entries are
removed in `finally`; invocation IDs cannot be reused within a capture run.
Association is not inferred from filenames, timestamps, test suffixes, Markdown
or verdicts.

Execution/invocation IDs are **wrapper-created association tokens**, not
upstream-issued Maester run IDs or cryptographic attestations. Three invocations
of the stable rule `EVAXIS.SYNTHETIC.1001` bind three explicit native targets:
Passed/completed-pass, Failed/completed-fail, and Skipped/not-run-unknown.
Only two supply source observations. These three preservation paths actually
executed. Generic result import, family expansion and arbitrary native error
capture are not claimed by this demo; other mapping branches are not a
provider-connected validation claim.

## Assembly, privacy and supported boundary

The CLI operations are:

```powershell
& $python capture\package.py validate-capture --input capture.json
& $python capture\package.py assemble --input capture.json --output new-bundle
& $python capture\package.py assemble --stdin --output new-bundle
& $python capture\package.py validate-package --input new-bundle\package.json
```

CLI capture validation and assembly require completed data; the schema also
represents collecting data in memory. Package validation accepts the plural
array wrapper, not arbitrary Maester results or a loose directory of records.
The original Core validator retains its legacy singular-fixture function
interface while adding multi-record support. Capture-lineage checks apply when
the reserved extension is present; generic v0.1 packages without it receive
only schema/package checks, not a claim of capture-lineage preservation.

Validation reports `schemaValidation` and `packageConsistency`, record counts,
`receiverVerification: not-performed`, and `sourceTruth: not-established`.
Valid `claims-verified` producer metadata remains only a producer assertion;
it never becomes receiver-established trust.

JSON is bounded to 1 MB input/per persisted file, nesting depth 32 and schema
array limits. Duplicate keys and non-finite numbers are rejected. Source
values are never included in custom validation errors. Known credential-named
fields and recognizable token/private-key patterns are rejected rather than
redacted or exported. This is a conservative guard, **not comprehensive DLP**;
other sensitive content still requires caller minimization and private storage.
Only finite JSON data is accepted, never scriptblocks, sessions or arbitrary
PowerShell objects.

Use a caller-approved, trusted local parent directory. Traversal components,
Windows UNC/device/alternate-stream and ambiguous names, mapped remote drives
and symlink/reparse paths are rejected. Inputs must be regular files;
Linux FIFO/device reads cannot block waiting for a writer. These checks are
not a complete network-filesystem or hostile-host detector.

Linux opens ancestors with directory/no-follow flags and holds their
descriptors. Input reads, private stage/file creation, no-replace rename and
cleanup are descriptor-relative. Windows opens verified non-reparse ancestors
with read access and without delete sharing, preventing ordinary ancestor
rename while the handles are held; input handles also reject final reparse
points. This mitigates selected path-substitution races, not arbitrary
privileged/same-identity filesystem manipulation.

Existing destinations, even empty directories, are refused. Random sibling
staging is private before payload writes: POSIX directory/file modes are
0700/0600 at creation, and Windows staging has a restricted owner ACL.
Files are flushed and fsynced; actual no-replace directory publication exposes
both complete JSON files together. Linux requires `renameat2(RENAME_NOREPLACE)`
and refuses unavailable kernel/filesystem support rather than falling back to
an overwriting rename.

Observable parent identity changes fail explicitly. Linux cleanup stays
anchored to the original parent instead of deleting through substituted paths.
If parent movement is detected after rename, no completion is claimed and a
complete bundle may remain in the original parent; it is not deleted to hide
the uncertain outcome. Cleanup failures report that incomplete private
staging may remain. No directory-fsync or power-loss guarantee is introduced.

| Configuration | Execution/support boundary |
|---|---|
| Local Windows, Python 3.13.16, PowerShell 7.6.9, NTFS | Current isolated execution passed, including real handle/reparse/no-overwrite races and genuine native capture. |
| CI Windows Server 2025 and Ubuntu 24.04 x64, Python 3.11/3.13 | Workflow configured; actual runner results must be recorded before claiming validation. |
| macOS | Publication unimplemented and explicitly refused; not a validated target. |
| Other OS/architectures/runtimes and untested filesystem configurations | Unvalidated; successful capability detection is not filesystem-trust certification. |
| Mapped/network storage, privileged or same-identity attackers, hostile mounts, crash durability and immutable storage | Not established or supported assurance claims. |

Wrapper-created Maester association tokens remain consistency checks, not
upstream identity or attestation. The owning runspace's capture session
remains mutable, not tamper-resistant. Packages are not promoted as suitable
for hostile or production collection environments.

No provider collector, hosted service, new storage backend, automatic upload,
authentication/authorization layer, encryption/signing, receiver verification,
retention/replay policy, comparison engine or Pack publication is implemented.
The next milestone is explicit review of the separate preservation proposal
and this machine contract before a separately authorized provider or receiver
implementation.

## Validation evidence

See the [test matrix and exact commands](../tests/capture/README.md).
All new outputs were genuinely produced and validated. The golden package was
generated through the pinned native path. The original lab separately executed
four static Pack checks and nine synthetic native rows; those are not live
provider or end-to-end preservation checks.

The original GitHub workflow still checks cARL governance only. The separate
[capture workflow](../.github/workflows/capture-validation.yml) now executes
the existing suites with [verified prerequisites](../tools/ci/README.md);
configured jobs are not reported as executed without actual runner evidence.
The current local Windows run discovered 130 Python cases, executed 121
successfully and explicitly skipped nine Linux-only cases; the required native
case executed. All 36 standalone PowerShell cases and conformance passed.
Local
cARL 1.0.2 diagnostics reported zero errors and 42 pre-existing canonical-byte
warnings, also reproduced on unmodified baseline snapshots with LF and CRLF.
Their cause is not established. Shared governance was not repaired or synced;
no shared policy, adapter, invariant, template, pack, runtime or original
governance workflow was repaired or changed. Repository-owned contract/plan,
memory and developer documentation are reconciled separately.
