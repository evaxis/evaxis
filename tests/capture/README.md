# Executable capture and preservation tests

The [complete golden capture/package](../../examples/evidence-preservation/golden/README.md)
is genuinely generated multi-record positive data. `cases.json` defines
**47 capture and 21 package rejection mutations** over those complete records.
They are data-driven fixtures, not executable code, loose record fragments,
or comparison-engine expectations.

## Commands

Use Python 3.11+, PowerShell 7.4+, and `requirements-dev.txt`; see
[fresh-checkout prerequisites](../../docs/evidence-preservation.md).
From the repository root, use `$python` from that prerequisite setup. For an
already configured environment, set `$python` to your trusted Python executable
(for example, `$python = (Get-Command python -ErrorAction Stop).Source`).
The commands below use Windows paths; the isolated runner provides portable
Windows/Linux reproduction with verified prerequisites.

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
& $python -B tools\validate_conformance.py
& $python -B -m unittest discover -s tests\capture -p 'test_*.py' -q
pwsh -NoProfile -File tests\capture\Test-Capture.ps1
```

Without `EVAXIS_MAESTER_SOURCE`, the one actual native integration test is
explicitly skipped. All other Python tests and all PowerShell cases run without
Maester; importing our narrow glue registry is not importing the engine.

To execute that additional integration test, first reproduce the
[pinned lab](../../tools/maester-lab/README.md), make its exact authentication
prerequisite available in `PSModulePath`, and set:

```powershell
$env:EVAXIS_MAESTER_SOURCE = Join-Path $lab 'refs\maester'
& $python -B -m unittest discover -s tests\capture -p 'test_*.py' -q
```

The integration test starts a fresh `pwsh -NoProfile`, runs the real native
callback three times, verifies run/result associations, writes a new private
bundle, and validates its two observations/three assessments. An intentional
native Failed conclusion and unavailable Skipped result are not suite failures.

## Historical v0.1 validation

The following results belong to the merged preservation experiment, not a
claim that unchanged historical counts describe the current suite.

| Layer | Executed result and meaning |
|---|---|
| Existing conformance | Four schema meta-checks, six valid and six expected-invalid records, 12 package rejection cases, and 22 semantic-expectation **data** checks. No comparison was executed. |
| New Python suite | 104 tests passed, zero skipped when the pinned source/module were supplied. Includes 68 mutation fixtures, positive cardinality/value/clock/lineage tests, filesystem/privacy/CLI tests, offline known/unknown runs and one native integration. |
| Standalone PowerShell | 36 behavioral cases passed without Maester; duplicate IDs, lifecycle, scope/time/reference/basis/coverage rejection, defensive copies, credentials, runspace ownership, one-use registry and native parameter/outcome association. |
| PowerShell parser | Eight new scripts/modules/manifests parsed with zero errors. This is static syntax validation. |
| Capture/assembly | Capture schema and its four referenced schemas meta-validated; golden capture and complete package validated, including preserved lineage and visibility projection. |
| Actual preservation-native run | Three invocations: one Passed, one Failed, one Skipped, with two captured observations and three associated assessments. |
| Original lab | Four `Test-MtPack` static checks passed; nine synthetic native rows and the sanitized fixture projection matched. No provider tests ran. |
| Hygiene | Existing validator now includes new capture/integration/example/test/docs files for local Markdown links, final newlines, trailing whitespace and common credential patterns; `git diff --check` also executed. |
| Local cARL | Doctor/status/effective/trace/harness diagnostics executed: zero errors, 42 pre-existing canonical-byte warnings on Windows, reproduced on unmodified LF and CRLF baseline snapshots. Cause unverified; no managed policy repair. |
| GitHub CI | Existing governance workflow only. Check the PR's actual check state; these locally executed capture suites are not automatically in that workflow. |

The measured environment was Windows, Python 3.13.16, PowerShell 7.6.9,
Maester 3.0.0 at the pinned commit, and Microsoft.Graph.Authentication 2.27.0
loaded only as a dependency. Source collection and evaluation were synthetic
and offline; no tenant, credentials, Pack publication or release was used.

## Assertions and negative cases

Identity/time tests reject missing or ambiguous authority, blank required
identifiers, absent object kind/native ID, display-only identity, foreign
scope/run, invalid/offset-free timestamps and wrong clock origins. Exact source
strings and case-sensitive data keys survive copying and assembly; a capture
event even 100 ns after its attempt completion is rejected.

Lifecycle/coverage tests reject duplicate runs in the explicit registry,
duplicate observations/attempts/assessments, unresolved attempts, reopened or
repeated completion, success despite failure, omitted expected targets,
duplicate/overlapping coverage and unknown inventory upgraded to complete.
Positive tests include partial coverage, explicit unknown inventory,
multiple observations per target, multiple assessments and an empty explicit
known scope without invented records.

Assessment/association tests reject unresolved references, wrong subject,
no legitimate input basis, no-input verdicts, execution-state/outcome
contradictions, wrong run/execution/invocation, reused context and mismatched
native parameters/results. A valid producer verification claim remains only
a producer assertion; report fields never become receiver trust.

Persistence/privacy tests reject oversized/deep/non-finite/duplicate-key JSON,
precision-losing decimal tokens, prohibited credential fields/recognizable
values, non-JSON objects, traversal and reparse ancestors. They assert
no-overwrite, competitor-destination preservation, cleanup and Windows private
ACLs. Sensitive sentinels never appear in safe exceptions or CLI diagnostics.
Corrupted envelope/record lineage and substituted visibility constraints fail.

Linux atomic publication and PowerShell on other operating systems were not
executed in that historical run. macOS publication, arbitrary privileged/hostile ancestor races, storage
immutability, cryptographic/receiver verification, semantic comparison and live
providers are not validated capabilities. Neither schema success nor the
intentionally synthetic verdicts establish source truth.

## Portable hardening validation

Use the [isolated runner and verified prerequisites](../../tools/ci/README.md)
to require the genuine native golden rather than accepting its optional skip.
The separate [capture workflow](../../.github/workflows/capture-validation.yml)
targets x64 `windows-2025` and `ubuntu-24.04`, Python 3.11 and 3.13. Actual
runtime/image/kernel/filesystem metadata and explicit skip reasons are
preserved in per-job minimized JSON reports.

| Current execution | Result |
|---|---|
| Local Windows, Python 3.13.16, PowerShell 7.6.9, NTFS | 130 Python cases discovered; 121 executed successfully; nine Linux-only skips. Genuine native golden executed; conformance and 36 PowerShell cases passed. |
| CI Windows Server 2025 x64, NTFS, Python 3.11.9/3.13.16, PowerShell 7.6.7 | Both jobs passed: 130 discovered, 121 executed, nine Linux-only skips; conformance, 36 PowerShell cases and genuine native golden passed. |
| CI Ubuntu 24.04 x64, Python 3.11.17/3.13.17, PowerShell 7.6.9 | Both jobs passed: 130 discovered, 126 executed, four Windows-only skips; conformance, 36 PowerShell cases and genuine native golden passed. |

The [four-job execution evidence](https://github.com/evaxis/evaxis/actions/runs/41337237522)
belongs to final implementation commit
`a417d5734e59162b0a069e40b56130e25e8c865c`. Measured runner images were
Windows `20261021.278.1` and Ubuntu `20261026.354.1`. Linux reported kernel
`7.0.0-1017-azure` and `stat -f -c %T` filesystem family `ext2/ext3`, not a
verified exact ext4 configuration. The Linux no-replace syscall, final-link/
ancestor replacement, FIFO and competing-publisher cases actually executed.

The initial Linux run found a directory-descriptor diagnostic/ownership gap.
Regular-file validation now precedes `fdopen`; the regression asserts no
stream is constructed for a directory and passed on all four configurations.

Additional regressions prove selected final-link and ancestor replacement
defenses, private file creation, regular-file/FIFO input rejection, concurrent
publisher winner preservation, safe anchored cleanup, explicit fsync/rename/
cleanup failures, unsupported publication refusal, dependency checksum tamper,
unsafe archives and actual extracted-byte verification.
The native test checks fresh output for exactly two observations and three
assessments, preserved source representations/timestamp strings/targets,
expected pass/fail/unknown conclusions and unchanged receiver/source-truth
values. Native-handle and temporary-directory cleanup failures are explicit.
Windows and Linux-specific skips are listed explicitly, not counted as passes.
The Linux class must execute its actual libc no-replace path on Linux; mocked
unsupported-primitive tests do not substitute for that execution.

No hostile-host/privileged-attacker, arbitrary filesystem, crash-durability,
session tamper-resistance, upstream attestation or receiver-trust guarantee is
introduced. macOS publication remains unsupported.

## Final-review regressions

The follow-up adds eight publication/cleanup regressions and nine aggregate
gate cases. The current suite discovers 147 cases. Local isolated Windows
executed 136 successfully, with 11 Linux-only skips, conformance, all 36
PowerShell cases and required native capture.

Primary publication/integrity errors remain primary when cleanup also fails;
safe notes preserve staging/handle failures and CLI output includes them.
Publication failure with successful cleanup, secondary deletion failure,
ancestor/descriptor close failure, cleanup-only close failure, uncertain
parent after successful rename, an unrelated caller exception handler and
clean/no-overwrite success are covered. Successful bodies do not inherit a
caller's already-handled exception as their own primary failure.
There is no ordinary success path with an unrenamed staging directory:
staging deletion runs on failure; after successful rename the source stage
no longer exists. The cleanup-only regression therefore exercises actual
post-rename descriptor/ancestor closure, not a fabricated deletion of the
published destination.

The [aggregate](../../tools/ci/README.md#merge-gate) rejects failed, cancelled,
skipped, neutral or missing matrix execution, each missing report, stale
commit/native results, malformed data and unexpected suite skips. It passes
only the exact four fresh successful reports plus a successful matrix result.
All cases use offline synthetic reports; actual workflow execution and
effective required-check configuration must be evidenced separately.
