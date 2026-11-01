# Reusable PowerShell capture helper

`Evaxis.Capture.psd1` exports nine explicit-session operations. PowerShell 7.4+
is required; Maester is not. In-memory collection has no Python requirement;
`Export-EvaxisCapture` uses a trusted Python executable and the existing pinned
validation dependency for full conformance before persistence.

```powershell
Import-Module .\integrations\powershell\Evaxis.Capture.psd1
Get-Command -Module Evaxis.Capture
```

See the [complete API/lifecycle and offline example](../../docs/evidence-preservation.md)
and [executable collector](../../examples/evidence-preservation/SyntheticCollector.ps1).
Use the public operations for mutation; read the versioned session document
only in process, never serialize session/runtime state. Source timestamps are
mandatory explicit strings, not automatic capture timestamps.

The helper checks identity, primary types, time origins, lifecycle, coverage
and evidence references; Python performs authoritative schema/package checks
before export. One session is single-writer and runspace-owned. Completion
is strict and non-idempotent; optional caller-owned run registries are not
durable replay protection. Credential guards are conservative, not complete
redaction or DLP.

Module version `0.1.0` describes this experimental implementation. It is not
a product release, approved architectural API or licensing decision.
