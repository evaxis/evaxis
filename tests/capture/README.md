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
(for example, `$python = (Get-Command python -ErrorAction Stop).Source`):

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

## Validation layers and observed results

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
executed. macOS publication, privileged/hostile ancestor races, storage
immutability, cryptographic/receiver verification, semantic comparison and live
providers are not validated capabilities. Neither schema success nor the
intentionally synthetic verdicts establish source truth.
