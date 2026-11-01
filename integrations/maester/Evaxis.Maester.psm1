Set-StrictMode -Version Latest
Import-Module (Join-Path $PSScriptRoot '..\powershell\Evaxis.Capture.psd1') -ErrorAction Stop
. (Join-Path $PSScriptRoot '..\..\examples\evidence-preservation\SyntheticCollector.ps1')

# Maester accepts scalar configuration parameters, not capture-session objects.
# This caller-runspace registry exists only around an explicitly bound invocation.
$script:Invocations = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)

function Register-EvaxisMaesterInvocation {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [hashtable] $Session,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Fixture,
        [Parameter(Mandatory)] [string] $NativeId,
        [Parameter(Mandatory)] [string] $ExecutionId,
        [Parameter(Mandatory)] [string] $InvocationId
    )
    if (-not $Session.Document.Contains('frameworkContext') -or
        $Session.Document.frameworkContext.executionId -cne $ExecutionId -or
        $Session.Document.state -cne 'collecting' -or
        $Session.OwnerRunspace -ne [runspace]::DefaultRunspace.InstanceId -or
        [string]::IsNullOrWhiteSpace($InvocationId) -or $script:Invocations.ContainsKey($InvocationId)) {
        throw 'EVX: duplicate or mismatched Maester invocation registration.'
    }
    if (-not $Session.ContainsKey('MaesterInvocationIds')) {
        $Session.MaesterInvocationIds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    }
    if (-not $Session.MaesterInvocationIds.Add($InvocationId)) {
        throw 'EVX: a Maester invocation ID cannot be reused within one capture run.'
    }
    $script:Invocations.Add($InvocationId, @{
        Session = $Session; Fixture = $Fixture; NativeId = $NativeId
        ExecutionId = $ExecutionId; CollectionRunId = $Session.Document.collectionRunId
        OwnerRunspace = [runspace]::DefaultRunspace.InstanceId; Consumed = $false
    })
}

function Assert-EvaxisMaesterResult {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [hashtable] $Session,
        [Parameter(Mandatory)] [string] $InvocationId,
        [Parameter(Mandatory)] [string] $NativeId,
        [Parameter(Mandatory)] [AllowEmptyCollection()] [object[]] $Rows
    )
    $assessments = @($Session.Document.assessments | Where-Object {
        $_.Contains('frameworkAssociation') -and $_.frameworkAssociation.invocationId -ceq $InvocationId
    })
    if ($Rows.Count -ne 1 -or $assessments.Count -ne 1) {
        throw 'EVX: native result/capture association requires exactly one row and assessment.'
    }
    $row = $Rows[0]
    $item = $assessments[0]
    $association = $item.frameworkAssociation
    if ($row.Id -cne $association.recordId -or $row.Result -cne $association.resultClaim -or
        $item.record.subject.nativeId -cne $NativeId -or
        $association.collectionRunId -cne $Session.Document.collectionRunId -or
        $association.executionId -cne $Session.Document.frameworkContext.executionId) {
        throw 'EVX: actual native result does not match its explicit capture association.'
    }
    $states = @{
        Passed = @('completed', 'pass'); Failed = @('completed', 'fail')
        Investigate = @('completed', 'unknown'); Error = @('failed', 'unknown')
        Skipped = @('not-run', 'unknown'); NotRun = @('not-run', 'unknown')
    }
    if (-not $states.ContainsKey($row.Result) -or
        $item.record.executionStatus -cne $states[$row.Result][0] -or
        $item.record.outcome -cne $states[$row.Result][1]) {
        throw 'EVX: native outcome contradicts the captured execution state or conclusion.'
    }
    if (-not $row.PSObject.Properties['Parameters']) {
        throw 'EVX: native result lacks explicit parameter association.'
    }
    $expected = [ordered]@{
        CollectionRunId = $Session.Document.collectionRunId
        ExecutionId = $Session.Document.frameworkContext.executionId
        InvocationId = $InvocationId
    }
    $parameters = @($row.Parameters)
    if ($parameters.Count -ne $expected.Count) {
        throw 'EVX: native result parameter association is incomplete or ambiguous.'
    }
    foreach ($name in $expected.Keys) {
        $matches = @($parameters | Where-Object { $_.Name -ceq $name })
        if ($matches.Count -ne 1 -or $matches[0].Value -isnot [string] -or
            $matches[0].Value -cne $expected[$name] -or $matches[0].Source -cne 'Parameter') {
            throw 'EVX: native result parameters do not match the explicit run and invocation.'
        }
    }
}

function Get-EvaxisMaesterInvocation {
    [CmdletBinding()]
    param([string] $CollectionRunId, [string] $ExecutionId, [string] $InvocationId)
    if ([string]::IsNullOrWhiteSpace($InvocationId) -or -not $script:Invocations.ContainsKey($InvocationId)) {
        throw 'EVX: Maester invocation has no registered capture context.'
    }
    $context = $script:Invocations[$InvocationId]
    if ($context.CollectionRunId -cne $CollectionRunId -or $context.ExecutionId -cne $ExecutionId -or
        $context.OwnerRunspace -ne [runspace]::DefaultRunspace.InstanceId -or $context.Consumed) {
        throw 'EVX: capture sidecar belongs to another run, execution, or completed invocation.'
    }
    $context.Consumed = $true
    return $context
}

function Unregister-EvaxisMaesterInvocation {
    [CmdletBinding()]
    param([Parameter(Mandatory)] [string] $InvocationId)
    if (-not $script:Invocations.Remove($InvocationId)) {
        throw 'EVX: Maester invocation cleanup did not find its registered context.'
    }
}

Export-ModuleMember -Function @(
    'Register-EvaxisMaesterInvocation', 'Get-EvaxisMaesterInvocation',
    'Unregister-EvaxisMaesterInvocation', 'Invoke-EvaxisSyntheticObject',
    'Assert-EvaxisMaesterResult'
)
