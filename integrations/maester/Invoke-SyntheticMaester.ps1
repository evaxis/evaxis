[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $MaesterSourcePath,
    [Parameter(Mandatory)] [string] $OutputDirectory,
    [string] $CollectionRunId = ([Guid]::NewGuid().ToString()),
    [string] $PythonCommand = 'python'
)
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion -lt [version]'7.4') { throw 'EVX: PowerShell 7.4 or later is required.' }
$pin = 'b8ad89557a831d3d3d7c369174300701243af8a6'
$head = & git -C $MaesterSourcePath rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $head -cne $pin) { throw 'EVX: Maester source does not match the reviewed immutable pin.' }
$dirty = & git -C $MaesterSourcePath status --porcelain --untracked-files=all
if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'EVX: pinned Maester source must be clean.' }
$modulePath = Join-Path $MaesterSourcePath 'powershell\Maester.psd1'
if ((Test-ModuleManifest -Path $modulePath).Version -ne [version]'3.0.0') {
    throw 'EVX: the pinned Maester manifest must declare version 3.0.0.'
}
if (-not @(Get-Module -ListAvailable -Name Microsoft.Graph.Authentication |
    Where-Object { $_.Version -eq [version]'2.27.0' }).Count) {
    throw 'EVX: the pinned lab prerequisite Microsoft.Graph.Authentication 2.27.0 is missing; this script never installs modules.'
}
$previousTelemetry = $env:MAESTER_DISABLE_TELEMETRY
$env:MAESTER_DISABLE_TELEMETRY = '1'
try {
    Import-Module (Join-Path $PSScriptRoot '..\powershell\Evaxis.Capture.psd1') -Force -ErrorAction Stop
    Import-Module (Join-Path $PSScriptRoot 'Evaxis.Maester.psm1') -Force -ErrorAction Stop
    . (Join-Path $PSScriptRoot '..\..\examples\evidence-preservation\SyntheticCollector.ps1')
    Import-Module Microsoft.Graph.Authentication -RequiredVersion 2.27.0 -ErrorAction Stop
    if ($null -ne (Get-MgContext -ErrorAction Stop)) {
        throw 'EVX: the offline proof requires a disconnected Graph session and never uses tenant credentials.'
    }
    $maester = Import-Module $modulePath -Force -PassThru -ErrorAction Stop
    if ($maester.Version -ne [version]'3.0.0') { throw 'EVX: imported Maester runtime is not version 3.0.0.' }
    $executionId = [Guid]::NewGuid().ToString()
    $run = New-EvaxisSyntheticRun -CollectionRunId $CollectionRunId -FrameworkContext @{
        authority = 'urn:maester365:maester'; id = 'native-engine'
        version = '3.0.0'; executionId = $executionId
    }
    $counts = @{ Passed = 0; Failed = 0; Skipped = 0 }
    foreach ($object in $run.Fixture.objects) {
        $invocationId = [Guid]::NewGuid().ToString()
        Register-EvaxisMaesterInvocation -Session $run.Session -Fixture $run.Fixture `
            -NativeId $object.target.nativeId -ExecutionId $executionId -InvocationId $invocationId
        try {
            $rows = @(Invoke-MtTest -Path (Join-Path $PSScriptRoot 'Test.EVAXIS.SYNTHETIC.1001.ps1') `
                -Id 'EVAXIS.SYNTHETIC.1001' -Parameter @{
                    CollectionRunId = $CollectionRunId; ExecutionId = $executionId; InvocationId = $invocationId
                } -ErrorAction Stop)
            Assert-EvaxisMaesterResult -Session $run.Session -InvocationId $invocationId -NativeId $object.target.nativeId -Rows $rows
            $counts[$rows[0].Result]++
        }
        finally { Unregister-EvaxisMaesterInvocation -InvocationId $invocationId }
    }
    if ($counts.Passed -ne 1 -or $counts.Failed -ne 1 -or $counts.Skipped -ne 1) {
        throw 'EVX: synthetic native execution did not return the expected Passed, Failed, and Skipped rows.'
    }
    Complete-EvaxisCapture -Session $run.Session -CollectionStatus 'partial' -CoverageStatus 'partial'
    $output = Export-EvaxisCapture -Session $run.Session -OutputDirectory $OutputDirectory -PythonCommand $PythonCommand
    [pscustomobject]@{
        CollectionRunId = $CollectionRunId; MaesterVersion = $maester.Version.ToString()
        PowerShellVersion = $PSVersionTable.PSVersion.ToString()
        NativeRows = $counts; OutputDirectory = $output.OutputDirectory; Validation = $output.Validation
    }
}
finally {
    if ($null -eq $previousTelemetry) { Remove-Item Env:MAESTER_DISABLE_TELEMETRY -ErrorAction SilentlyContinue }
    else { $env:MAESTER_DISABLE_TELEMETRY = $previousTelemetry }
}
