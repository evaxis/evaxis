# Portable synthetic validation

The [capture workflow](../../.github/workflows/capture-validation.yml) is
separate from unchanged governance. It targets x64 Windows Server 2025 and
Ubuntu 24.04 with Python 3.11 and 3.13, recording actual image/runtime/kernel
and filesystem observations. A configured workflow is not execution evidence;
see [measured results](../../tests/capture/README.md).

## Isolation and prerequisites

Each job uses a fresh GitHub-hosted runner, read-only contents permission,
no secrets, no persisted checkout credentials, no shared dependency cache,
and no release/deployment permissions. PR jobs use `pull_request`, never
`pull_request_target`. Push jobs permit branch verification without a PR.
Actions are pinned to full commits; reports have 14-day retention.

`requirements-validation.txt` locks the existing jsonschema validation
dependency and its transitive dependencies to reviewed PyPI wheel hashes.
`--require-hashes --only-binary=:all:` rejects substitution and source builds.
No new product dependency or Pester framework is introduced.

`native-dependencies.json` pins the existing Maester 3.0.0 source commit and
Graph Authentication 2.27.0 package. Preparation verifies SHA-256 of the
complete 752-file executable Maester module tree and the downloaded Graph
package before any module import. The module-tree digest combines sorted Git
UTF-8 paths, a NUL separator and each file's SHA-256 bytes. Checkout line-ending
conversion is disabled. Archive traversal, links, normalized/duplicate paths
and excessive expansion fail before extraction. The runner rechecks actual
native/extracted bytes before executing tests.

The source/package hashes were obtained from the exact public GitHub commit
and official PowerShell Gallery package, respectively; they bind reviewed
bytes, not publisher identity, signatures or collector attestation.
Prerequisites remain outside the Core checkout. Runtime scripts do not install
modules, connect to tenants or publish evidence.

Networked preparation is separate from synthetic execution. The runner exposes
only its verified module directory and PowerShell's built-in module directory;
native execution refuses a connected Graph context and disables telemetry.
These controls do not claim OS-enforced egress isolation or protection against
a compromised runner. Only the reviewed synthetic callbacks are invoked.

## Reproduce the CI execution locally

Use an approved Python 3.11/3.13 and PowerShell 7.4+ installation. In PowerShell,
from the Core root, choose fresh private directories outside the checkout:

```powershell
$base = Join-Path ([IO.Path]::GetTempPath()) ('evaxis-validation-' + [Guid]::NewGuid())
New-Item -ItemType Directory -Path $base -ErrorAction Stop | Out-Null
$venv = Join-Path $base 'venv'
python -m venv $venv
$python = if ($IsWindows) { Join-Path $venv 'Scripts\python.exe' } else { Join-Path $venv 'bin/python' }
& $python -m pip --disable-pip-version-check install --require-hashes --only-binary=:all: --no-cache-dir -r tools/ci/requirements-validation.txt
& $python -B tools/ci/prepare_validation.py --workspace (Join-Path $base 'native')
& $python -B tools/ci/run_validation.py --workspace (Join-Path $base 'native') --report (Join-Path $base 'report.json')
```

Check each command's exit status; do not execute the runner after failed
preparation. The preparation workspace must be new. A verified workspace can
be reused for another runner invocation, which rechecks integrity and uses a
new temporary test directory.

The runner executes conformance, Python capture/integrity regressions, the
genuine native golden and all standalone PowerShell cases. Native execution
must actually start and finish; missing prerequisites or unexpected skips
fail the job. Windows-only/Linux-only cases are explicitly skipped on the
other OS and listed in the report, never counted as passes.

Reports contain synthetic suite results and platform metadata, not raw capture
packages or customer evidence. A native Failed conclusion and unavailable
Skipped assessment are expected synthetic outcomes, not test-suite failures.
Passing checks establish neither source truth nor receiver verification.

## Merge gate

`Capture validation gate` always runs after the four `synthetic` matrix jobs.
It requires the matrix dependency to conclude `success` and checks exactly
four fresh, successful report artifacts for the current commit, required
native execution, conformance, Python/PowerShell results and unchanged trust
disclaimers. Opposite-platform test skips are allowed explicitly; skipped
jobs, missing reports, native skips, failures, cancellation, neutral results
and stale reports do not pass. No `continue-on-error` or job/path filter is
used. Downloading same-run reports adds no Actions token permissions.

GitHub accepts `skipped` and `neutral` required status checks, so the four
matrix check names alone are not sufficient. Require these six GitHub Actions
checks on `main-foundations`, with strict up-to-date checks:

- `cARL governance`
- `Synthetic capture (windows-2025, Python 3.11)`
- `Synthetic capture (windows-2025, Python 3.13)`
- `Synthetic capture (ubuntu-24.04, Python 3.11)`
- `Synthetic capture (ubuntu-24.04, Python 3.13)`
- `Capture validation gate`

The existing active ruleset must retain its PR-only updates, empty bypass list,
zero required approvals, review-thread resolution, deletion/non-fast-forward
protection and existing merge methods. The additive owner update does not
introduce a sole-maintainer approval deadlock. UI configuration: Settings >
Rules > Rulesets > main-foundations > Require status checks to pass; add
the exact six names, select GitHub Actions as source (app ID 15368), retain
Require branches to be up to date before merging, then save and inspect the
effective branch rules. Do not add bypass actors.

No merge queue is configured. All currently permitted merge/squash/rebase
paths are subject to the same ruleset; direct pushes are constrained by its
PR requirement. Do not exercise a bypass to test this. A future merge queue
requires separately reviewed `merge_group` execution.

Required checks are not tamper-proof validation: maintainer review must protect
the workflow, checker, report generator and exact four-job matrix. A repository
administrator can edit rules later; no perpetual administrator-resistance
claim is made. Removing a required workflow normally leaves missing checks
blocking merge. Deliberately rewriting a required job to skip or return a
false success remains a workflow-review boundary, not a protection provided by
ordinary required-status rules. Organisation ruleset enumeration may require
`admin:org`; use effective branch rules and report visibility limitations.
