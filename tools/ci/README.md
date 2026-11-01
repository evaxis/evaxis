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
