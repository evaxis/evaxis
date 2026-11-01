# Optional synthetic Maester-native proof

This is one native synthetic test and a narrow invocation wrapper, not a
Maester Pack or an arbitrary result importer. Core capture and the reusable
PowerShell module do not depend on Maester.

Use Maester 3.0.0 at exact source commit
`b8ad89557a831d3d3d7c369174300701243af8a6`, PowerShell 7.4+, and the declared
`Microsoft.Graph.Authentication` 2.27.0 prerequisite. Follow the
[fresh-checkout instructions](../../docs/evidence-preservation.md) and
[pinned lab](../../tools/maester-lab/README.md).

```powershell
$output = Join-Path $env:TEMP ('evaxis-native-' + [Guid]::NewGuid())
pwsh -NoProfile -File integrations\maester\Invoke-SyntheticMaester.ps1 `
  -MaesterSourcePath $env:EVAXIS_MAESTER_SOURCE -OutputDirectory $output
```

The wrapper verifies the clean source pin, refuses a connected Graph context,
and disables telemetry. An owned, one-use context registry supplies actual
source facts to the callback through explicit run/execution/invocation tokens.
Native `Parameters` carry only those scalar tokens, not capture/session state.
Actual row identity, parameters, subject and outcome must match the captured
assessment before export. Context is removed in `finally`; reuse is rejected.

The source is captured **inside** the native callback before it returns its
normal result. Three actual invocations yield Passed, Failed and Skipped.
Only the first two produce observations; Skipped retains unavailable collection
and not-run/unknown assessment. Returned verdicts or Markdown never become
observations. The wrapper-created tokens are not upstream Maester run IDs,
authenticated association or independent verification.

The pinned native parser requires only function definitions at the test file's
top level and a neighboring Markdown file. Scalar parameters are deliberate;
no upstream internal type becomes the Core abstraction.
Other Maester versions, generic/family/error exports, live providers and Pack
publication are unsupported by this example.
