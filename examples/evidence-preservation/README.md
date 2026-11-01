# Synthetic evidence preservation example

`synthetic-source.json` is explicitly fictional. Two policies share a display
name but have distinct native IDs and historical source timestamps. Their
preserved `enabled` booleans produce separate pass/fail conclusions. A third
declared candidate is unavailable and has no source payload or observation time.

`SyntheticCollector.ps1` records those facts and actual attempt/capture events
through the reusable helper before evaluation. `Invoke-OfflineExample.ps1`
requires no Maester. The optional native callback exercises the same collector
and rule through a genuinely executing pinned Maester engine.

```powershell
$output = Join-Path $env:TEMP ('evaxis-offline-' + [Guid]::NewGuid())
pwsh -NoProfile -File examples\evidence-preservation\Invoke-OfflineExample.ps1 `
  -OutputDirectory $output
```

Prerequisites, a private Python-environment option, native invocation and the
supported boundary are in [developer instructions](../../docs/evidence-preservation.md).
Use `-InventoryStatus unknown` with a new directory for legitimate unknown
coverage. Export never overwrites an existing destination or automatically
uploads evidence.

The [golden package](golden/README.md) was produced by actual native execution.
It is synthetic producer evidence, not a receiver-verified assurance claim or
an approved architectural contract.
