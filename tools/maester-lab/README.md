# Offline Maester compatibility lab

This tracked verification tool reproduces the synthetic compatibility
observations documented in `docs/maester-compatibility.md`. It is research
tooling, not Core runtime code, an adapter, an Evaxis conformance test or a
provider-connected compatibility test.

## Pinned references

| Repository | Owner / default branch | Commit | License |
|---|---|---|---|
| [maester](https://github.com/maester365/maester) | `maester365` / `main` | `b8ad89557a831d3d3d7c369174300701243af8a6` | MIT |
| [maester-pack-demo](https://github.com/maester365/maester-pack-demo) | `maester365` / `main` | `3f83cc8b674ac7c195f4611473e21bec6c50e8f3` | MIT |
| [maester-pack-lpms](https://github.com/Mynster9361/maester-pack-lpms) | `Mynster9361` / `main` | `f6aa60d98cc8b0efab233b7332d1269a4bd9690c` | MIT |
| [maester-pack-rksolutions](https://github.com/royklo/maester-pack-rksolutions) | `royklo` / `main` | `852a83b1b57fc2490d8d5554d7ca6102504b63d4` | MIT |

The script initializes independent checkouts, fetches only the listed commits,
checks each resulting `HEAD`, and refuses modified, mismatched or unexpected
existing checkouts. It does not vendor upstream source or follow a moving
branch.

## Prerequisites

- PowerShell 7.4 or later (verified here with 7.6.0).
- Git with HTTPS access to the four public GitHub repositories.
- Maester's declared `Microsoft.Graph.Authentication` 2.27.0 prerequisite
  already available in the PowerShell module path.
- The pinned Maester source includes its prebuilt engine; rebuilding it is not
  part of this verification. Rebuilding upstream source requires the .NET SDK
  version recorded in its `global.json`.

The script does not install PowerShell modules, Maester Packs, .NET SDKs or
other dependencies. Satisfy prerequisites from an approved source before
running it. The Maester authentication module is loaded only as a declared
dependency; the selected tests do not invoke it or call Microsoft Graph.

## Run

From a fresh Core checkout:

```powershell
pwsh -NoProfile -File tools/maester-lab/verify-maester.ps1
```

By default, pinned checkouts and full native result rows are written beneath
`~/.cache/evaxis-maester-lab`, outside the repository. On Unix-like systems,
the script restricts the output directory to the current user. Choose a new
workspace if an existing reference checkout is not clean and at its required
commit:

```powershell
pwsh -NoProfile -File tools/maester-lab/verify-maester.ps1 `
  -WorkspacePath /tmp/evaxis-maester-lab
```

The tracked privacy-safe projection is compared by default. To run the runtime
assertions without comparing that fixture:

```powershell
pwsh -NoProfile -File tools/maester-lab/verify-maester.ps1 -SkipProjection
```

## What executes and what is asserted

The script statically validates the demo, built-in Zero Trust Assessment,
LPMS and RK Intune Packs with `Test-MtPack`. It then invokes only the reviewed
synthetic demo IDs `MP.DEMO.1001`–`1006` and `MP.DEMO.1009`. It expects nine
rows: Passed, Failed, Investigate, configured Skipped, Error,
`ServiceNotConnected` Skipped, and three family instances. It checks the
disconnected reason plus `ParentId`/`InstanceId`, and compares only fields
present in the Core projection. The fixture is a sanitized projection, not raw
Maester output and not an executable adapter test.

It does not execute Graph-dependent test 1007; the long-running/report
attachment example 1008; LPMS or RK tenant tests; Pack installation/update;
`Connect-Maester`; `Invoke-Maester`; tenant-connected collection; or
publication. The offline checks do not prove source collection, assessment
correctness, coverage or provider compatibility. Only source inspection and
static validation are claimed for the unexecuted features.
Any future privileged or tenant-connected experiment is outside this tool and
requires separate explicit authorization and its own reviewed execution plan.

Maester telemetry is disabled before module import. The only network activity
intended by this script is fetching the exact public Git commits. It never
prompts for, reads, stores or prints credentials. Full native rows remain in
the user-local output file and are not suitable for publication without
separate privacy review. The command's console summary contains IDs, statuses
and family references only.
