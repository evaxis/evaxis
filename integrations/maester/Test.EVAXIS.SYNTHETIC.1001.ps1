function Test-EvaxisSyntheticPolicy {
    [MaesterTest(
        Id = 'EVAXIS.SYNTHETIC.1001',
        Title = 'Synthetic source policy has its enabled setting',
        Severity = 'Low',
        Product = 'Synthetic',
        Feature = 'evidence-preservation',
        Area = 'offline-example',
        ResourceType = 'SyntheticPolicy'
    )]
    [CmdletBinding()]
    [OutputType([bool])]
    param([string] $CollectionRunId, [string] $ExecutionId, [string] $InvocationId)

    Import-Module (Join-Path $PSScriptRoot 'Evaxis.Maester.psm1') -ErrorAction Stop
    $context = Get-EvaxisMaesterInvocation -CollectionRunId $CollectionRunId -ExecutionId $ExecutionId -InvocationId $InvocationId
    $result = Invoke-EvaxisSyntheticObject -Session $context.Session -Fixture $context.Fixture `
        -NativeId $context.NativeId `
        -Evaluator @{ authority = 'urn:maester365:maester'; id = 'native-engine'; version = '3.0.0' } `
        -FrameworkAssociation @{
            executionId = $ExecutionId; invocationId = $InvocationId
            collectionRunId = $CollectionRunId; recordId = 'EVAXIS.SYNTHETIC.1001'
        }
    if ($result.NativeResult -ceq 'Skipped') {
        Add-MtTestResultDetail -SkippedBecause Custom -SkippedCustomReason 'Synthetic source unavailable; no security conclusion.'
        return
    }
    Add-MtTestResultDetail -Result 'The synthetic rule used the source observation preserved by the evidence helper.'
    return $result.BooleanResult
}
