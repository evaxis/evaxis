[CmdletBinding()]
param(
    [string] $WorkspacePath,
    [switch] $SkipProjection
)

$ErrorActionPreference = 'Stop'

if ($PSVersionTable.PSVersion -lt [version]'7.4') {
    throw 'PowerShell 7.4 or later is required.'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'Git is required to fetch the pinned source commits.'
}

$coreRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if (-not $WorkspacePath) {
    $WorkspacePath = Join-Path $HOME '.cache/evaxis-maester-lab'
}
$workspace = [System.IO.Path]::GetFullPath($WorkspacePath)
$corePrefix = $coreRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
    [System.IO.Path]::DirectorySeparatorChar
if ($workspace.Equals($coreRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
    $workspace.StartsWith($corePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The lab workspace must be outside the Core checkout so raw outputs stay untracked.'
}

$references = @(
    @{
        Name = 'maester'
        Uri = 'https://github.com/maester365/maester'
        Commit = 'b8ad89557a831d3d3d7c369174300701243af8a6'
    },
    @{
        Name = 'maester-pack-demo'
        Uri = 'https://github.com/maester365/maester-pack-demo'
        Commit = '3f83cc8b674ac7c195f4611473e21bec6c50e8f3'
    },
    @{
        Name = 'maester-pack-lpms'
        Uri = 'https://github.com/Mynster9361/maester-pack-lpms'
        Commit = 'f6aa60d98cc8b0efab233b7332d1269a4bd9690c'
    },
    @{
        Name = 'maester-pack-rksolutions'
        Uri = 'https://github.com/royklo/maester-pack-rksolutions'
        Commit = '852a83b1b57fc2490d8d5554d7ca6102504b63d4'
    }
)

function Invoke-Git {
    param(
        [string] $RepositoryPath,
        [string[]] $GitArguments
    )

    $output = & git -C $RepositoryPath @GitArguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Git failed in '$RepositoryPath': $($GitArguments -join ' ')`n$($output -join "`n")"
    }
    return ($output | Out-String).Trim()
}

function Get-PinnedCheckout {
    param([hashtable] $Reference)

    $path = Join-Path (Join-Path $workspace 'refs') $Reference.Name
    if (-not (Test-Path -LiteralPath $path)) {
        $null = New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force
        $null = & git init --quiet $path
        if ($LASTEXITCODE -ne 0) {
            throw "Could not initialize the pinned checkout '$($Reference.Name)'."
        }
        Invoke-Git -RepositoryPath $path -GitArguments @('remote', 'add', 'origin', $Reference.Uri) | Out-Null
        Invoke-Git -RepositoryPath $path -GitArguments @('fetch', '--depth=1', 'origin', $Reference.Commit) | Out-Null
        Invoke-Git -RepositoryPath $path -GitArguments @('checkout', '--detach', 'FETCH_HEAD') | Out-Null
    }
    else {
        if (-not (Test-Path -LiteralPath (Join-Path $path '.git'))) {
            throw "Existing reference path is not a Git checkout: $path"
        }
        $origin = Invoke-Git -RepositoryPath $path -GitArguments @('remote', 'get-url', 'origin')
        if ($origin -ne $Reference.Uri) {
            throw "Unexpected origin for '$($Reference.Name)': $origin"
        }
        $dirty = Invoke-Git -RepositoryPath $path -GitArguments @('status', '--porcelain', '--untracked-files=all')
        if ($dirty) {
            throw "Pinned reference checkout is modified: $path"
        }
        $head = Invoke-Git -RepositoryPath $path -GitArguments @('rev-parse', 'HEAD')
        if ($head -ne $Reference.Commit) {
            throw "Existing '$($Reference.Name)' checkout is at $head, not pinned commit $($Reference.Commit). Use a new workspace."
        }
    }

    $head = Invoke-Git -RepositoryPath $path -GitArguments @('rev-parse', 'HEAD')
    if ($head -ne $Reference.Commit) {
        throw "Pin verification failed for '$($Reference.Name)': expected $($Reference.Commit), received $head."
    }
    return $path
}

$previousPrompt = $env:GIT_TERMINAL_PROMPT
$env:GIT_TERMINAL_PROMPT = '0'
try {
    $checkoutPaths = @{}
    foreach ($reference in $references) {
        $checkoutPaths[$reference.Name] = Get-PinnedCheckout -Reference $reference
        Write-Output "Pinned $($reference.Name): $($reference.Commit)"
    }
}
finally {
    if ($null -eq $previousPrompt) {
        Remove-Item Env:GIT_TERMINAL_PROMPT -ErrorAction SilentlyContinue
    }
    else {
        $env:GIT_TERMINAL_PROMPT = $previousPrompt
    }
}

$maesterRoot = $checkoutPaths['maester']
$demoRoot = $checkoutPaths['maester-pack-demo']
$modulePath = Join-Path $maesterRoot 'powershell/Maester.psd1'
$moduleManifest = Test-ModuleManifest -Path $modulePath
if ($moduleManifest.Version -ne [version]'3.0.0') {
    throw "Expected pinned Maester 3.0.0; found $($moduleManifest.Version)."
}
$authModule = Get-Module -ListAvailable -Name Microsoft.Graph.Authentication |
    Where-Object { $_.Version -eq [version]'2.27.0' } |
    Select-Object -First 1
if (-not $authModule) {
    throw 'Microsoft.Graph.Authentication 2.27.0 is a declared Maester prerequisite. Install it separately from an approved source; this script never installs modules.'
}

$previousTelemetry = $env:MAESTER_DISABLE_TELEMETRY
$env:MAESTER_DISABLE_TELEMETRY = '1'
try {
    $module = Import-Module $modulePath -Force -PassThru
    if ($module.Version -ne [version]'3.0.0') {
        throw "Imported Maester version mismatch: $($module.Version)."
    }

    foreach ($commandName in 'Test-MtPack', 'Invoke-MtTest') {
        if (-not (Get-Command $commandName -ErrorAction SilentlyContinue)) {
            throw "$commandName is not exported by the pinned Maester module."
        }
    }

    $packChecks = @(
        @{ Name = 'demo'; Path = $demoRoot; Official = $true },
        @{
            Name = 'zero-trust-assessment'
            Path = (Join-Path $maesterRoot 'packs/zero-trust-assessment')
            Official = $true
        },
        @{
            Name = 'lpms'
            Path = $checkoutPaths['maester-pack-lpms']
            Official = $false
        },
        @{
            Name = 'rksolutions-intune'
            Path = (Join-Path $checkoutPaths['maester-pack-rksolutions'] 'intune-anomalies')
            Official = $false
        }
    )
    foreach ($pack in $packChecks) {
        $result = Test-MtPack -Path $pack.Path -Official:$pack.Official
        if (-not $result.IsValid) {
            throw "Test-MtPack rejected '$($pack.Name)'."
        }
        Write-Output "Pack structure valid: $($pack.Name) ($($result.Id) $($result.Version); risk $($result.Risk))"
    }

    $syntheticIds = @(
        'MP.DEMO.1001',
        'MP.DEMO.1002',
        'MP.DEMO.1003',
        'MP.DEMO.1004',
        'MP.DEMO.1005',
        'MP.DEMO.1006',
        'MP.DEMO.1009'
    )
    $rows = @(Invoke-MtTest -Path $demoRoot -Id $syntheticIds)
    if ($rows.Count -ne 9) {
        throw "Expected 9 synthetic native result rows; received $($rows.Count)."
    }

    $expectedResults = @{
        'MP.DEMO.1001' = 'Passed'
        'MP.DEMO.1002' = 'Failed'
        'MP.DEMO.1003' = 'Investigate'
        'MP.DEMO.1004' = 'Skipped'
        'MP.DEMO.1005' = 'Error'
        'MP.DEMO.1006' = 'Skipped'
        'MP.DEMO.1009.app-one' = 'Passed'
        'MP.DEMO.1009.app-two' = 'Failed'
        'MP.DEMO.1009.app-three' = 'Passed'
    }
    $rowsById = @{}
    foreach ($row in $rows) {
        if ($rowsById.ContainsKey($row.Id)) {
            throw "Duplicate native result row ID '$($row.Id)'."
        }
        $rowsById[$row.Id] = $row
    }
    foreach ($id in $expectedResults.Keys) {
        if (-not $rowsById.ContainsKey($id)) {
            throw "Expected synthetic native result row '$id' was not returned."
        }
        if ($rowsById[$id].Result -ne $expectedResults[$id]) {
            throw "Unexpected result for '$id': $($rowsById[$id].Result)."
        }
    }
    if ($rowsById.Count -ne $expectedResults.Count) {
        throw 'Received unexpected native result row IDs.'
    }
    if ($rowsById['MP.DEMO.1006'].ReasonCode -ne 'ServiceNotConnected') {
        throw 'The disconnected connector did not produce ServiceNotConnected.'
    }
    foreach ($suffix in 'app-one', 'app-two', 'app-three') {
        $id = "MP.DEMO.1009.$suffix"
        if ($rowsById[$id].ParentId -ne 'MP.DEMO.1009' -or
            $rowsById[$id].InstanceId -ne $id) {
            throw "Family identity was not preserved for '$id'."
        }
    }

    $outputPath = Join-Path $workspace 'outputs'
    $null = New-Item -ItemType Directory -Path $outputPath -Force
    if ($IsLinux -or $IsMacOS) {
        [System.IO.File]::SetUnixFileMode(
            $outputPath,
            [System.IO.UnixFileMode]::UserRead -bor
                [System.IO.UnixFileMode]::UserWrite -bor
                [System.IO.UnixFileMode]::UserExecute
        )
    }
    $resultPath = Join-Path $outputPath "demo-native-results-$([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')).json"
    $rows | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $resultPath -Encoding utf8
    if ($IsLinux -or $IsMacOS) {
        [System.IO.File]::SetUnixFileMode(
            $resultPath,
            [System.IO.UnixFileMode]::UserRead -bor [System.IO.UnixFileMode]::UserWrite
        )
    }

    if (-not $SkipProjection) {
        $projectionPath = Join-Path $coreRoot 'tests/fixtures/maester-v3/native-result-projection.json'
        $projection = Get-Content -LiteralPath $projectionPath -Raw | ConvertFrom-Json
        if ($projection.captureFormat -ne 'evaxis.maester-native-result-projection/0.1' -or
            $projection.synthetic -ne $true) {
            throw 'Projection fixture has an unsupported format or is not marked synthetic.'
        }

        $fixtureRows = @($projection.rows)
        if ($fixtureRows.Count -ne $rows.Count) {
            throw "Projection fixture has $($fixtureRows.Count) rows; expected $($rows.Count)."
        }
        foreach ($fixtureRow in $fixtureRows) {
            if (-not $rowsById.ContainsKey($fixtureRow.Id)) {
                throw "Projection fixture contains unknown row '$($fixtureRow.Id)'."
            }
            $runtimeRow = $rowsById[$fixtureRow.Id]
            foreach ($property in $fixtureRow.PSObject.Properties) {
                $runtimeProperty = $runtimeRow.PSObject.Properties[$property.Name]
                if ($null -eq $runtimeProperty -or
                    (ConvertTo-Json -InputObject $runtimeProperty.Value -Depth 20 -Compress) -cne
                    (ConvertTo-Json -InputObject $property.Value -Depth 20 -Compress)) {
                    throw "Projection mismatch for '$($fixtureRow.Id)' field '$($property.Name)'."
                }
            }
        }
        Write-Output 'Sanitized Core projection matches the synthetic runtime rows.'
    }

    Write-Output "PowerShell: $($PSVersionTable.PSVersion); Maester: $($module.Version)"
    Write-Output 'Synthetic row assertions passed: 9 rows; disconnected reason; 3 family identities.'
    Write-Output "Full synthetic rows are local only: $resultPath"
    $rows |
        Sort-Object Id |
        Select-Object Id, Result, ReasonCode, ParentId, InstanceId |
        Format-Table -AutoSize |
        Out-String |
        Write-Output
}
finally {
    if ($null -eq $previousTelemetry) {
        Remove-Item Env:MAESTER_DISABLE_TELEMETRY -ErrorAction SilentlyContinue
    }
    else {
        $env:MAESTER_DISABLE_TELEMETRY = $previousTelemetry
    }
}
