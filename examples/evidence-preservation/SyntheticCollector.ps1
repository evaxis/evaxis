function Convert-EvaxisSyntheticElement {
    [CmdletBinding()]
    param([System.Text.Json.JsonElement] $Element, [int] $Depth = 0)
    if ($Depth -gt 32) { throw 'EVX: synthetic JSON exceeds the nesting limit.' }
    switch ($Element.ValueKind.ToString()) {
        'Object' {
            $result = [Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
            foreach ($property in $Element.EnumerateObject()) {
                if ($result.Contains($property.Name)) { throw 'EVX: duplicate synthetic JSON property.' }
                $result.Add($property.Name, (Convert-EvaxisSyntheticElement $property.Value ($Depth + 1)))
            }
            return $result
        }
        'Array' {
            $result = @()
            foreach ($item in $Element.EnumerateArray()) { $result += ,(Convert-EvaxisSyntheticElement $item ($Depth + 1)) }
            return ,$result
        }
        'String' { return $Element.GetString() }
        'True' { return $true }
        'False' { return $false }
        'Null' { return $null }
        'Number' {
            $value = [long]0
            if (-not $Element.TryGetInt64([ref]$value)) { throw 'EVX: this synthetic fixture supports only exact integer numbers.' }
            return $value
        }
        default { throw 'EVX: unsupported synthetic JSON value.' }
    }
}

function New-EvaxisSyntheticRun {
    [CmdletBinding()]
    param(
        [string] $CollectionRunId = ([Guid]::NewGuid().ToString()),
        [string] $InventoryStatus = 'known',
        [System.Collections.IDictionary] $FrameworkContext
    )
    $sourcePath = Join-Path $PSScriptRoot 'synthetic-source.json'
    if ((Get-Item -LiteralPath $sourcePath -ErrorAction Stop).Length -gt 1000000) {
        throw 'EVX: synthetic fixture exceeds the 1 MB input limit.'
    }
    $json = Get-Content -LiteralPath $sourcePath -Raw -ErrorAction Stop
    # ConvertFrom-Json can coerce ISO timestamps into DateTime and lose their
    # supplied offset/spelling. JsonElement preserves the source string on 7.4+.
    $document = [System.Text.Json.JsonDocument]::Parse($json)
    try { $fixture = Convert-EvaxisSyntheticElement $document.RootElement }
    finally { $document.Dispose() }
    if ($fixture.synthetic -ne $true -or $fixture.fixtureVersion -cne '1') {
        throw 'EVX: only the reviewed synthetic source fixture is supported.'
    }
    $targets = @($fixture.objects | ForEach-Object {
        @{ authority = $_.target.authority; scopeId = $_.target.scopeId; nativeId = $_.target.nativeId }
    })
    $arguments = @{
        Collector = @{
            authority = 'urn:evaxis:synthetic-collector'; id = 'offline-policy-collector'
            version = '0.1.0'; identityClaimStatus = 'asserted'
        }
        Source = $fixture.source; RequestedScope = $fixture.requestedScope
        ExpectedTargets = $targets; CollectionRunId = $CollectionRunId
        InventoryStatus = $InventoryStatus
        InventoryBasis = 'Declared fixture candidates only. No real provider inventory or whole-environment completeness is claimed.'
        CollectorConfiguration = @{ version = 'synthetic-fixture/1' }
    }
    if ($FrameworkContext) { $arguments.FrameworkContext = $FrameworkContext }
    return @{ Session = New-EvaxisCaptureSession @arguments; Fixture = $fixture }
}

function Invoke-EvaxisSyntheticObject {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [hashtable] $Session,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Fixture,
        [Parameter(Mandatory)] [string] $NativeId,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Evaluator,
        [System.Collections.IDictionary] $FrameworkAssociation
    )
    if ($Fixture.synthetic -ne $true) { throw 'EVX: source is not explicitly synthetic.' }
    $matches = @($Fixture.objects | Where-Object { $_.target.nativeId -ceq $NativeId })
    if ($matches.Count -ne 1) { throw 'EVX: synthetic native identity is missing or ambiguous.' }
    $object = $matches[0]
    $target = $object.target
    $subject = @{ authority = $target.authority; scopeId = $target.scopeId; nativeId = $target.nativeId; kind = $target.kind }
    $attemptId = 'attempt:' + $NativeId
    $observationId = 'observation:' + $NativeId
    $assessmentId = 'assessment:' + $NativeId
    Start-EvaxisSourceAttempt -Session $Session -AttemptId $attemptId -IntendedTargets @($subject)
    $assessment = @{
        Session = $Session; AssessmentId = $assessmentId; Subject = $subject
        Rule = @{ authority = 'urn:evaxis:synthetic-rule'; id = 'EVAXIS.SYNTHETIC.1001'; version = '0.1.0' }
        Evaluator = $Evaluator; TimestampOrigin = 'evaluator-event'
        ClockBasis = 'Actual evaluator event on the local UTC clock; no external clock or freshness verification.'
    }
    if ($object.availability -ceq 'available') {
        Add-EvaxisObservation -Session $Session -AttemptId $attemptId -ObservationId $observationId `
            -Target $target -ObservedAt $object.observedAt -TimestampOrigin 'synthetic-fixture' `
            -ClockBasis $Fixture.clockBasis -ObservationType 'configuration' `
            -ObservationSchema $Fixture.observationSchema -Representation $object.representation
        Complete-EvaxisSourceAttempt -Session $Session -AttemptId $attemptId -Status 'succeeded'
        $captured = @($Session.Document.observations | Where-Object { $_.record.observationId -ceq $observationId })[0]
        $assessment.AssessedAt = [DateTimeOffset]::UtcNow.ToString('o')
        $enabled = $captured.record.representation.content.enabled
        if ($enabled -isnot [bool]) { throw 'EVX: synthetic policy setting is not a source-native boolean.' }
        $outcome = if ($enabled) { 'pass' } else { 'fail' }
        $nativeResult = if ($enabled) { 'Passed' } else { 'Failed' }
        $assessment.ExecutionStatus = 'completed'; $assessment.Outcome = $outcome
        $assessment.ObservationReferences = @($observationId)
        $assessment.InputBasis = @{ kind = 'observations'; rationale = 'Rule evaluates only the preserved enabled boolean of this exact source-native target.' }
        $assessment.ControlCoverage = @{ status = 'complete'; assessedSubjects = @($subject); unassessedSubjects = @() }
    }
    elseif ($object.availability -cin @('denied', 'unavailable', 'unsupported', 'not-attempted')) {
        Complete-EvaxisSourceAttempt -Session $Session -AttemptId $attemptId -Status $object.availability `
            -Limitation @{ code = 'synthetic-' + $object.availability; description = 'The fixture explicitly models a source visibility limitation; no source payload was received.' } `
            -VisibilityConstraints @(@{ kind = 'source-limit'; description = 'Synthetic target availability is declared in the reviewed fixture.' })
        Add-EvaxisNotObservedTarget -Session $Session -AttemptId $attemptId -Target $subject -Reason $object.availability
        $assessment.AssessedAt = [DateTimeOffset]::UtcNow.ToString('o')
        $nativeResult = 'Skipped'
        $assessment.ExecutionStatus = 'not-run'; $assessment.Outcome = 'unknown'
        $assessment.ObservationReferences = @()
        $assessment.InputBasis = @{ kind = 'no-input'; rationale = 'Source evidence was not available; the security rule was not evaluated.' }
        $assessment.ControlCoverage = @{
            status = 'unknown'; assessedSubjects = @()
            unassessedSubjects = @(@{ target = $subject; reason = 'missing-evidence' })
        }
    }
    else { throw 'EVX: unsupported synthetic source availability.' }
    if ($FrameworkAssociation) {
        $association = @{} + $FrameworkAssociation
        $association.resultClaim = $nativeResult
        $assessment.FrameworkAssociation = $association
    }
    Add-EvaxisAssessment @assessment
    return [pscustomobject]@{
        NativeResult = $nativeResult; AssessmentId = $assessmentId
        ObservationId = $(if ($nativeResult -cne 'Skipped') { $observationId } else { $null })
        BooleanResult = $(if ($nativeResult -cne 'Skipped') { $enabled } else { $null })
    }
}
