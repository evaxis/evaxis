[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $OutputDirectory,
    [string] $CollectionRunId = ([Guid]::NewGuid().ToString()),
    [string] $InventoryStatus = 'known',
    [string] $PythonCommand = 'python'
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot '..\..\integrations\powershell\Evaxis.Capture.psd1') -Force -ErrorAction Stop
. (Join-Path $PSScriptRoot 'SyntheticCollector.ps1')
$run = New-EvaxisSyntheticRun -CollectionRunId $CollectionRunId -InventoryStatus $InventoryStatus
$evaluator = @{ authority = 'urn:evaxis:synthetic-evaluator'; id = 'offline-policy-check'; version = '0.1.0' }
foreach ($object in $run.Fixture.objects) {
    Invoke-EvaxisSyntheticObject -Session $run.Session -Fixture $run.Fixture -NativeId $object.target.nativeId -Evaluator $evaluator | Out-Null
}
Complete-EvaxisCapture -Session $run.Session -CollectionStatus 'partial' `
    -CoverageStatus $(if ($InventoryStatus -ceq 'unknown') { 'unknown' } else { 'partial' })
Export-EvaxisCapture -Session $run.Session -OutputDirectory $OutputDirectory -PythonCommand $PythonCommand
