[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
Import-Module (Join-Path $root 'integrations\powershell\Evaxis.Capture.psd1') -Force
. (Join-Path $root 'examples\evidence-preservation\SyntheticCollector.ps1')
$script:Passed = 0

function Assert-True {
    [CmdletBinding()]
    param([bool] $Condition)
    if (-not $Condition) { throw 'Synthetic assertion failed.' }
}

function Assert-Rejected {
    [CmdletBinding()]
    param([scriptblock] $Action, [string] $Message)
    $caught = $null
    try { & $Action | Out-Null }
    catch { $caught = $_.Exception.Message }
    if ($null -eq $caught -or -not $caught.Contains($Message)) {
        throw 'Expected precise boundary rejection was not observed.'
    }
}

function Invoke-Case {
    [CmdletBinding()]
    param([string] $Name, [scriptblock] $Action)
    try { & $Action; $script:Passed++ }
    catch { throw "Capture test '$Name' failed: $($_.Exception.Message)" }
}

function New-ObservationArguments {
    [CmdletBinding()]
    param([hashtable] $Run)
    return @{
        Session = $Run.Session; AttemptId = 'attempt-one'; ObservationId = 'observation-one'
        Target = $Run.Fixture.objects[0].target; ObservedAt = $Run.Fixture.objects[0].observedAt
        TimestampOrigin = 'synthetic-fixture'; ClockBasis = $Run.Fixture.clockBasis
        ObservationType = 'configuration'; ObservationSchema = $Run.Fixture.observationSchema
        Representation = $Run.Fixture.objects[0].representation
    }
}

function New-ObservedRun {
    [CmdletBinding()]
    param([System.Collections.IDictionary] $FrameworkContext)
    $arguments = @{}
    if ($FrameworkContext) { $arguments.FrameworkContext = $FrameworkContext }
    $run = New-EvaxisSyntheticRun @arguments
    Invoke-EvaxisSyntheticObject -Session $run.Session -Fixture $run.Fixture `
        -NativeId $run.Fixture.objects[0].target.nativeId `
        -Evaluator @{ authority = 'urn:synthetic:evaluator'; id = 'test-evaluator'; version = '1' } | Out-Null
    return $run
}

function New-AssessmentArguments {
    [CmdletBinding()]
    param([hashtable] $Run)
    $record = $Run.Session.Document.assessments[0].record
    return @{
        Session = $Run.Session; AssessmentId = 'new-assessment'; Subject = $record.subject
        Rule = $record.rule; Evaluator = $record.evaluator; AssessedAt = [DateTimeOffset]::UtcNow.ToString('o')
        TimestampOrigin = 'evaluator-event'; ClockBasis = 'Local synthetic evaluator event.'
        ExecutionStatus = $record.executionStatus; Outcome = $record.outcome
        ObservationReferences = $record.observationReferences; InputBasis = $record.inputBasis
        ControlCoverage = $record.controlCoverage
    }
}

Invoke-Case 'duplicate run identity in explicit registry' {
    $run = New-EvaxisSyntheticRun
    $registry = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $arguments = @{
        Collector = $run.Session.Document.collector; Source = $run.Fixture.source
        RequestedScope = $run.Fixture.requestedScope; ExpectedTargets = $run.Session.Document.inventory.expectedTargets
        InventoryStatus = 'known'; InventoryBasis = 'Synthetic declared candidates.'
        CollectionRunId = 'duplicate-run'; RunRegistry = $registry
    }
    New-EvaxisCaptureSession @arguments | Out-Null
    Assert-Rejected { New-EvaxisCaptureSession @arguments } 'duplicate collection run'
}
Invoke-Case 'duplicate attempt' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'one' -IntendedTargets @($run.Fixture.objects[0].target)
    Assert-Rejected { Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'one' -IntendedTargets @($run.Fixture.objects[0].target) } 'duplicate source attempt'
}
Invoke-Case 'duplicate observation' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -IntendedTargets @($run.Fixture.objects[0].target)
    $arguments = New-ObservationArguments $run
    Add-EvaxisObservation @arguments
    Assert-Rejected { Add-EvaxisObservation @arguments } 'duplicate observation'
}
Invoke-Case 'observation wrong run' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -IntendedTargets @($run.Fixture.objects[0].target)
    $arguments = New-ObservationArguments $run
    $arguments.CollectionRunId = 'another-run'
    Assert-Rejected { Add-EvaxisObservation @arguments } 'another run'
}
Invoke-Case 'source timestamp preserves exact lexical value' {
    $run = New-ObservedRun
    Assert-True ($run.Session.Document.observations[0].record.observedAt -ceq '2026-01-02T03:03:00Z')
    Assert-True ($run.Session.Document.observations[0].capturedAt -cne $run.Session.Document.observations[0].record.observedAt)
}
Invoke-Case 'invalid source timestamp' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -IntendedTargets @($run.Fixture.objects[0].target)
    $arguments = New-ObservationArguments $run
    $arguments.ObservedAt = 'invalid'
    Assert-Rejected { Add-EvaxisObservation @arguments } 'timestamp must be'
}
Invoke-Case 'missing native ID and display-only identity' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -IntendedTargets @($run.Fixture.objects[0].target)
    $arguments = New-ObservationArguments $run
    $arguments.Target = @{ displayName = 'Synthetic policy'; authority = 'urn:evaxis:synthetic-source'; scopeId = 'synthetic-workspace' }
    Assert-Rejected { Add-EvaxisObservation @arguments } 'required identifier'
}
Invoke-Case 'foreign target authority' {
    $run = New-EvaxisSyntheticRun
    Assert-Rejected {
        Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'one' -IntendedTargets @(
            @{ authority = 'another-authority'; scopeId = 'synthetic-workspace'; nativeId = 'synthetic-policy-001' }
        )
    } 'outside the declared'
}
Invoke-Case 'unresolved attempt at completion' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'one' -IntendedTargets @($run.Fixture.objects[0].target)
    Assert-Rejected { Complete-EvaxisCapture -Session $run.Session -CollectionStatus 'partial' -CoverageStatus 'unknown' } 'unresolved source attempts'
}
Invoke-Case 'success cannot omit intended target' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'one' -IntendedTargets @($run.Fixture.objects[0].target)
    Assert-Rejected { Complete-EvaxisSourceAttempt -Session $run.Session -AttemptId 'one' -Status 'succeeded' } 'observe every intended target'
}
Invoke-Case 'repeated attempt completion' {
    $run = New-ObservedRun
    Assert-Rejected { Complete-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt:synthetic-policy-001' -Status 'succeeded' } 'completed source attempts'
}
Invoke-Case 'observation cannot reopen completed attempt' {
    $run = New-ObservedRun
    $arguments = New-ObservationArguments $run
    $arguments.AttemptId = 'attempt:synthetic-policy-001'
    Assert-Rejected { Add-EvaxisObservation @arguments } 'completed source attempts'
}
Invoke-Case 'denied attempt cannot contain observation' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -IntendedTargets @($run.Fixture.objects[0].target)
    $arguments = New-ObservationArguments $run
    Add-EvaxisObservation @arguments
    Assert-Rejected {
        Complete-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -Status 'denied' `
            -Limitation @{ code = 'synthetic-denied'; description = 'Synthetic denial.' }
    } 'non-collecting attempt'
}
Invoke-Case 'missing limitation fails explicitly' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'one' -IntendedTargets @($run.Fixture.objects[0].target)
    Assert-Rejected { Complete-EvaxisSourceAttempt -Session $run.Session -AttemptId 'one' -Status 'denied' } 'requires a minimized limitation'
}
Invoke-Case 'complete coverage cannot omit expected targets' {
    $run = New-ObservedRun
    Assert-Rejected { Complete-EvaxisCapture -Session $run.Session -CollectionStatus 'succeeded' -CoverageStatus 'complete' } 'coverage contradicts'
}
Invoke-Case 'duplicate assessment' {
    $run = New-ObservedRun
    $arguments = New-AssessmentArguments $run
    $arguments.AssessmentId = $run.Session.Document.assessments[0].record.assessmentId
    Assert-Rejected { Add-EvaxisAssessment @arguments } 'duplicate assessment'
}
Invoke-Case 'unresolved observation reference' {
    $run = New-ObservedRun
    $arguments = New-AssessmentArguments $run
    $arguments.ObservationReferences = @('missing-observation')
    Assert-Rejected { Add-EvaxisAssessment @arguments } 'unresolved'
}
Invoke-Case 'assessment wrong subject' {
    $run = New-ObservedRun
    $arguments = New-AssessmentArguments $run
    $arguments.Subject = @{
        authority = 'urn:evaxis:synthetic-source'; scopeId = 'synthetic-workspace'; nativeId = 'synthetic-policy-002'
    }
    Assert-Rejected { Add-EvaxisAssessment @arguments } 'subject-matching evidence'
}
Invoke-Case 'execution failure is not control Fail' {
    $run = New-ObservedRun
    $arguments = New-AssessmentArguments $run
    $arguments.ExecutionStatus = 'failed'; $arguments.Outcome = 'fail'
    Assert-Rejected { Add-EvaxisAssessment @arguments } 'status and outcome contradict'
}
Invoke-Case 'verdict without legitimate basis' {
    $run = New-ObservedRun
    $arguments = New-AssessmentArguments $run
    $arguments.InputBasis = @{ kind = 'no-input'; rationale = 'No available input.' }
    $arguments.ObservationReferences = @()
    Assert-Rejected { Add-EvaxisAssessment @arguments } 'conclusion contradicts'
}
Invoke-Case 'sensitive content is never included in diagnostic' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -IntendedTargets @($run.Fixture.objects[0].target)
    $arguments = New-ObservationArguments $run
    $arguments.Representation = @{ encoding = 'json'; content = @{ sensitiveValue = 'synthetic-sensitive-never-log' } }
    $arguments.ObservedAt = 'invalid'
    $message = ''
    try { Add-EvaxisObservation @arguments } catch { $message = $_.Exception.Message }
    Assert-True ($message.Contains('timestamp must be') -and -not $message.Contains('synthetic-sensitive-never-log'))
}
Invoke-Case 'credential fields are prohibited' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -IntendedTargets @($run.Fixture.objects[0].target)
    $arguments = New-ObservationArguments $run
    $arguments.Representation = @{ encoding = 'json'; content = @{ AccessToken = 'synthetic-sensitive-never-log' } }
    Assert-Rejected { Add-EvaxisObservation @arguments } 'prohibited credential field'
    Assert-True ($run.Session.Document.observations.Count -eq 0)
}
Invoke-Case 'recognizable credential values are prohibited without logging' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -IntendedTargets @($run.Fixture.objects[0].target)
    $arguments = New-ObservationArguments $run
    $arguments.Representation = @{ encoding = 'json'; content = @{ value = 'ghp_' + ('x' * 36) } }
    Assert-Rejected { Add-EvaxisObservation @arguments } 'prohibited credential value'
    Assert-True ($run.Session.Document.observations.Count -eq 0)
}
Invoke-Case 'PowerShell session state is not serializable evidence' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -IntendedTargets @($run.Fixture.objects[0].target)
    $arguments = New-ObservationArguments $run
    $arguments.Representation = @{ encoding = 'json'; content = @{ unsafe = { 'synthetic' } } }
    Assert-Rejected { Add-EvaxisObservation @arguments } 'only finite JSON'
}
Invoke-Case 'captured representation is defensively copied' {
    $run = New-ObservedRun
    $run.Fixture.objects[0].representation.content.enabled = $false
    Assert-True ($run.Session.Document.observations[0].record.representation.content.enabled -eq $true)
}
Invoke-Case 'case-sensitive source object keys are preserved' {
    $run = New-EvaxisSyntheticRun
    Start-EvaxisSourceAttempt -Session $run.Session -AttemptId 'attempt-one' -IntendedTargets @($run.Fixture.objects[0].target)
    $arguments = New-ObservationArguments $run
    $content = [Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
    $content.Add('Setting', 1); $content.Add('setting', 2)
    $arguments.Representation = @{ encoding = 'json'; content = $content }
    Add-EvaxisObservation @arguments
    $captured = $run.Session.Document.observations[0].record.representation.content
    Assert-True ($captured.Count -eq 2 -and $captured['Setting'] -eq 1 -and $captured['setting'] -eq 2)
}
Invoke-Case 'unknown inventory remains unknown' {
    $run = New-EvaxisSyntheticRun -InventoryStatus 'unknown'
    foreach ($object in $run.Fixture.objects) {
        Invoke-EvaxisSyntheticObject -Session $run.Session -Fixture $run.Fixture -NativeId $object.target.nativeId `
            -Evaluator @{ authority = 'urn:synthetic:evaluator'; id = 'test'; version = '1' } | Out-Null
    }
    Assert-Rejected { Complete-EvaxisCapture -Session $run.Session -CollectionStatus 'partial' -CoverageStatus 'complete' } 'coverage contradicts'
    Complete-EvaxisCapture -Session $run.Session -CollectionStatus 'partial' -CoverageStatus 'unknown'
    Assert-True ((Get-EvaxisCaptureDocument $run.Session).coverageStatus -ceq 'unknown')
    Assert-Rejected { Complete-EvaxisCapture -Session $run.Session -CollectionStatus 'partial' -CoverageStatus 'unknown' } 'cannot be reopened'
}
Invoke-Case 'incomplete capture cannot export' {
    $run = New-EvaxisSyntheticRun
    Assert-Rejected { Get-EvaxisCaptureDocument -Session $run.Session } 'only completed capture documents'
}
Invoke-Case 'explicit unknown failure does not imply observation' {
    $run = New-EvaxisSyntheticRun
    Invoke-EvaxisSyntheticObject -Session $run.Session -Fixture $run.Fixture -NativeId 'synthetic-policy-003' `
        -Evaluator @{ authority = 'urn:synthetic:evaluator'; id = 'test'; version = '1' } | Out-Null
    Assert-True ($run.Session.Document.observations.Count -eq 0)
    Assert-True ($run.Session.Document.assessments[0].record.outcome -ceq 'unknown')
    Assert-True ($run.Session.Document.assessments[0].record.executionStatus -ceq 'not-run')
}
Invoke-Case 'framework sidecar rejects wrong run' {
    $run = New-ObservedRun -FrameworkContext @{ authority = 'urn:synthetic:framework'; id = 'test'; version = '1'; executionId = 'execution-one' }
    $arguments = New-AssessmentArguments $run
    $arguments.FrameworkAssociation = @{
        collectionRunId = 'another-run'; executionId = 'execution-one'; invocationId = 'one'
        recordId = 'synthetic-record'; resultClaim = 'opaque'
    }
    Assert-Rejected { Add-EvaxisAssessment @arguments } 'sidecar belongs to another run'
}
Invoke-Case 'explicitly empty framework association is not silently omitted' {
    $run = New-ObservedRun -FrameworkContext @{ authority = 'urn:synthetic:framework'; id = 'test'; version = '1'; executionId = 'execution-one' }
    $arguments = New-AssessmentArguments $run
    $arguments.FrameworkAssociation = @{}
    Assert-Rejected { Add-EvaxisAssessment @arguments } 'sidecar belongs to another run'
}
Invoke-Case 'explicitly empty optional run context fails' {
    $run = New-EvaxisSyntheticRun
    $arguments = @{
        Collector = $run.Session.Document.collector; Source = $run.Fixture.source
        RequestedScope = $run.Fixture.requestedScope; ExpectedTargets = $run.Session.Document.inventory.expectedTargets
        InventoryStatus = 'known'; InventoryBasis = 'Synthetic declared candidates.'
        CollectorConfiguration = @{}
    }
    Assert-Rejected { New-EvaxisCaptureSession @arguments } 'required identifier'
    $arguments.Remove('CollectorConfiguration')
    $arguments.FrameworkContext = @{}
    Assert-Rejected { New-EvaxisCaptureSession @arguments } 'required identifier'
}
Invoke-Case 'same display names remain distinct native subjects' {
    $run = New-EvaxisSyntheticRun
    Assert-True ($run.Fixture.objects[0].target.displayName -ceq $run.Fixture.objects[1].target.displayName)
    Assert-True ($run.Session.TargetKeys.Count -eq 3)
}
Invoke-Case 'shared session mutation across runspaces is rejected' {
    $run = New-EvaxisSyntheticRun
    $shell = [powershell]::Create()
    try {
        $null = $shell.AddScript({
            param($ModulePath, $Capture)
            $ErrorActionPreference = 'Stop'
            Import-Module $ModulePath
            Start-EvaxisSourceAttempt -Session $Capture -AttemptId 'foreign-runspace' -IntendedTargets @()
        }).AddArgument((Join-Path $root 'integrations\powershell\Evaxis.Capture.psd1')).AddArgument($run.Session)
        $caught = ''
        try { $null = $shell.Invoke() } catch { $caught = $_.Exception.Message }
        if ($shell.Streams.Error.Count) { $caught += $shell.Streams.Error[0].Exception.Message }
        Assert-True ($caught.Contains('cannot be shared across runspaces') -and $run.Session.Document.sourceAttempts.Count -eq 0)
    }
    finally { $shell.Dispose() }
}

Import-Module (Join-Path $root 'integrations\maester\Evaxis.Maester.psm1') -Force
Invoke-Case 'one-use invocation registry rejects wrong run and replay' {
    $run = New-EvaxisSyntheticRun -FrameworkContext @{ authority = 'urn:synthetic:framework'; id = 'test'; version = '1'; executionId = 'execution-one' }
    Register-EvaxisMaesterInvocation -Session $run.Session -Fixture $run.Fixture -NativeId 'synthetic-policy-001' -ExecutionId 'execution-one' -InvocationId 'invocation-one'
    try {
        Assert-Rejected {
            Get-EvaxisMaesterInvocation -CollectionRunId 'another-run' -ExecutionId 'execution-one' -InvocationId 'invocation-one'
        } 'another run'
        $context = Get-EvaxisMaesterInvocation -CollectionRunId $run.Session.Document.collectionRunId -ExecutionId 'execution-one' -InvocationId 'invocation-one'
        Assert-True ([object]::ReferenceEquals($context.Session, $run.Session))
        Assert-Rejected {
            Get-EvaxisMaesterInvocation -CollectionRunId $run.Session.Document.collectionRunId -ExecutionId 'execution-one' -InvocationId 'invocation-one'
        } 'completed invocation'
    }
    finally { Unregister-EvaxisMaesterInvocation -InvocationId 'invocation-one' }
    Assert-Rejected {
        Register-EvaxisMaesterInvocation -Session $run.Session -Fixture $run.Fixture -NativeId 'synthetic-policy-001' -ExecutionId 'execution-one' -InvocationId 'invocation-one'
    } 'cannot be reused'
    Assert-Rejected {
        Get-EvaxisMaesterInvocation -CollectionRunId $run.Session.Document.collectionRunId -ExecutionId 'execution-one' -InvocationId 'invocation-one'
    } 'no registered capture context'
}
Invoke-Case 'native row and sidecar outcome must agree' {
    $run = New-ObservedRun -FrameworkContext @{ authority = 'urn:synthetic:framework'; id = 'test'; version = '1'; executionId = 'execution-one' }
    $run.Session.Document.assessments[0].frameworkAssociation = @{
        collectionRunId = $run.Session.Document.collectionRunId; executionId = 'execution-one'
        invocationId = 'assertion-test'; recordId = 'EVAXIS.SYNTHETIC.1001'; resultClaim = 'Passed'
    }
    $row = [pscustomobject]@{
        Id = 'EVAXIS.SYNTHETIC.1001'; Result = 'Failed'; Parameters = @(
            [pscustomobject]@{ Name = 'CollectionRunId'; Value = $run.Session.Document.collectionRunId; Source = 'Parameter' }
            [pscustomobject]@{ Name = 'ExecutionId'; Value = 'execution-one'; Source = 'Parameter' }
            [pscustomobject]@{ Name = 'InvocationId'; Value = 'assertion-test'; Source = 'Parameter' }
        )
    }
    Assert-Rejected {
        Assert-EvaxisMaesterResult -Session $run.Session -InvocationId 'assertion-test' -NativeId 'synthetic-policy-001' -Rows @($row)
    } 'does not match'
    $row.Result = 'Passed'
    $run.Session.Document.assessments[0].record.outcome = 'fail'
    Assert-Rejected {
        Assert-EvaxisMaesterResult -Session $run.Session -InvocationId 'assertion-test' -NativeId 'synthetic-policy-001' -Rows @($row)
    } 'contradicts'
    $run.Session.Document.assessments[0].record.outcome = 'pass'
    Assert-EvaxisMaesterResult -Session $run.Session -InvocationId 'assertion-test' -NativeId 'synthetic-policy-001' -Rows @($row)
    $row.Parameters[2].Value = 'another-invocation'
    Assert-Rejected {
        Assert-EvaxisMaesterResult -Session $run.Session -InvocationId 'assertion-test' -NativeId 'synthetic-policy-001' -Rows @($row)
    } 'parameters do not match'
}
[pscustomobject]@{ PowerShellCaptureTests = $script:Passed; Failed = 0; MaesterRequired = $false }
