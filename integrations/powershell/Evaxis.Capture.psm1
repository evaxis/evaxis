Set-StrictMode -Version Latest

function Copy-EvaxisJson {
    [CmdletBinding()]
    param([AllowNull()] $Value, [int] $Depth = 0)

    if ($Depth -gt 32) { throw 'EVX: JSON nesting exceeds the capture limit.' }
    if ($null -eq $Value) { return $null }
    if ($Value -is [System.Collections.IDictionary]) {
        $copy = [Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
        foreach ($key in $Value.Keys) {
            if ($key -isnot [string] -or ($key -replace '[-_]', '').ToLowerInvariant() -in @(
                'accesstoken', 'refreshtoken', 'authorization', 'clientsecret',
                'password', 'privatekey', 'credential', 'credentials',
                'token', 'secret', 'apikey', 'secretkey', 'sharedaccesssignature', 'connectionstring'
            )) {
                throw 'EVX: non-string or prohibited credential field.'
            }
            $copy[$key] = Copy-EvaxisJson -Value $Value[$key] -Depth ($Depth + 1)
        }
        return $copy
    }
    if ($Value -is [array]) {
        $copy = @()
        foreach ($item in $Value) { $copy += ,(Copy-EvaxisJson -Value $item -Depth ($Depth + 1)) }
        return ,$copy
    }
    if ($Value -is [string]) {
        if ($Value -match '-----BEGIN [A-Z ]*PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b|(?i)\bBearer\s+[A-Za-z0-9._~+/-]{24,}') {
            throw 'EVX: prohibited credential value.'
        }
        return $Value
    }
    if ($Value -is [bool] -or
        $Value -is [byte] -or $Value -is [sbyte] -or
        $Value -is [short] -or $Value -is [ushort] -or
        $Value -is [int] -or $Value -is [uint] -or
        $Value -is [long] -or $Value -is [ulong] -or
        $Value -is [decimal]) { return $Value }
    if (($Value -is [double] -or $Value -is [single]) -and [double]::IsFinite($Value)) { return $Value }
    throw 'EVX: only finite JSON primitives, dictionaries, arrays, and null are supported.'
}

function Assert-EvaxisIdentifier {
    [CmdletBinding()]
    param([AllowNull()] $Value, [int] $Maximum = 256)
    if ($Value -isnot [string] -or [string]::IsNullOrWhiteSpace($Value) -or $Value.Length -gt $Maximum) {
        throw 'EVX: required identifier is missing, ambiguous, or too long.'
    }
}

function Assert-EvaxisTime {
    [CmdletBinding()]
    param([string] $Value)
    $parsed = [DateTimeOffset]::MinValue
    if ($Value -cnotmatch '^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:[0-5]\d)$' -or -not [DateTimeOffset]::TryParse(
        $Value, [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::None, [ref]$parsed
    )) { throw 'EVX: timestamp must be a valid date-time with an explicit UTC offset.' }
    return $parsed
}

function Get-EvaxisNow {
    [CmdletBinding()]
    param()
    return [DateTimeOffset]::UtcNow.ToString('o', [Globalization.CultureInfo]::InvariantCulture)
}

function Assert-EvaxisSession {
    [CmdletBinding()]
    param([hashtable] $Session, [switch] $AllowCompleted)
    if (-not $Session.ContainsKey('Marker') -or $Session.Marker -cne 'evaxis.capture-session/0.1') {
        throw 'EVX: expected an explicit capture session.'
    }
    if ($Session.OwnerRunspace -ne [runspace]::DefaultRunspace.InstanceId) {
        throw 'EVX: one capture session cannot be shared across runspaces.'
    }
    if (-not $AllowCompleted -and $Session.Document.state -cne 'collecting') {
        throw 'EVX: completed capture runs cannot be reopened or changed.'
    }
}

function Get-EvaxisTargetReference {
    [CmdletBinding()]
    param([System.Collections.IDictionary] $Target)
    $reference = [ordered]@{}
    foreach ($key in 'authority', 'scopeId', 'nativeId') {
        Assert-EvaxisIdentifier $Target[$key]
        $reference[$key] = $Target[$key]
    }
    if ($Target.Contains('displayName')) {
        if ($Target['displayName'] -isnot [string]) { throw 'EVX: display name must be text.' }
        $reference.displayName = $Target['displayName']
    }
    return $reference
}

function Get-EvaxisTargetKey {
    [CmdletBinding()]
    param([System.Collections.IDictionary] $Target)
    $reference = Get-EvaxisTargetReference $Target
    return ConvertTo-Json -InputObject @(
        $reference.authority, $reference.scopeId, $reference.nativeId
    ) -Compress
}

function Assert-EvaxisDeclaredTarget {
    [CmdletBinding()]
    param([hashtable] $Session, [System.Collections.IDictionary] $Target)
    $key = Get-EvaxisTargetKey $Target
    if (-not $Session.TargetKeys.Contains($key)) {
        throw 'EVX: target is outside the declared authority, scope, or native candidate set.'
    }
    return $key
}

function Get-EvaxisAttempt {
    [CmdletBinding()]
    param([hashtable] $Session, [string] $AttemptId, [switch] $AllowCompleted)
    Assert-EvaxisIdentifier $AttemptId
    $matches = @($Session.Document.sourceAttempts | Where-Object { $_.attemptId -ceq $AttemptId })
    if ($matches.Count -ne 1) { throw 'EVX: source attempt does not resolve.' }
    $attempt = $matches[0]
    if (-not $AllowCompleted -and $attempt.status -cne 'in-progress') {
        throw 'EVX: completed source attempts cannot be reopened or completed again.'
    }
    return $attempt
}

function Assert-EvaxisVersionedIdentity {
    [CmdletBinding()]
    param([System.Collections.IDictionary] $Identity)
    foreach ($key in 'authority', 'id', 'version') { Assert-EvaxisIdentifier $Identity[$key] }
}

function New-EvaxisCaptureSession {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Collector,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Source,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $RequestedScope,
        [Parameter(Mandatory)] [AllowEmptyCollection()] [object[]] $ExpectedTargets,
        [Parameter(Mandatory)] [string] $InventoryStatus,
        [Parameter(Mandatory)] [string] $InventoryBasis,
        [string] $CollectionRunId = ([Guid]::NewGuid().ToString()),
        [System.Collections.Generic.HashSet[string]] $RunRegistry,
        [System.Collections.IDictionary] $CollectorConfiguration,
        [System.Collections.IDictionary] $FrameworkContext
    )
    Assert-EvaxisIdentifier $CollectionRunId -Maximum 240
    Assert-EvaxisVersionedIdentity $Collector
    if ($Collector['identityClaimStatus'] -notin @('asserted', 'claims-authenticated', 'unverified', 'claims-invalid', 'unknown')) {
        throw 'EVX: collector identity claim status is required.'
    }
    foreach ($key in 'authority', 'scopeId') {
        Assert-EvaxisIdentifier $Source[$key]
        Assert-EvaxisIdentifier $RequestedScope[$key]
        if ($Source[$key] -cne $RequestedScope[$key]) { throw 'EVX: source and requested scope differ.' }
    }
    if ($InventoryStatus -cnotin @('known', 'unknown') -or [string]::IsNullOrWhiteSpace($InventoryBasis)) {
        throw 'EVX: explicit inventory status and basis are required.'
    }
    $keys = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $targets = @()
    foreach ($target in $ExpectedTargets) {
        $reference = Get-EvaxisTargetReference $target
        if ($reference.authority -cne $Source['authority'] -or $reference.scopeId -cne $Source['scopeId']) {
            throw 'EVX: candidate target belongs to another authority or scope.'
        }
        if (-not $keys.Add((Get-EvaxisTargetKey $reference))) { throw 'EVX: duplicate candidate target identity.' }
        $targets += ,$reference
    }
    $document = [ordered]@{
        captureContractVersion = '0.1'; envelopeContractVersion = '0.1'
        collectionRunId = $CollectionRunId; state = 'collecting'
        collector = Copy-EvaxisJson $Collector; source = Copy-EvaxisJson $Source
        requestedScope = Copy-EvaxisJson $RequestedScope; startedAt = Get-EvaxisNow
        inventory = [ordered]@{ status = $InventoryStatus; basis = $InventoryBasis; expectedTargets = $targets }
        sourceAttempts = @(); observations = @(); notObserved = @(); assessments = @()
    }
    if ($null -ne $CollectorConfiguration) {
        Assert-EvaxisIdentifier $CollectorConfiguration['version']
        $document.collectorConfiguration = Copy-EvaxisJson $CollectorConfiguration
    }
    if ($null -ne $FrameworkContext) {
        Assert-EvaxisVersionedIdentity $FrameworkContext
        Assert-EvaxisIdentifier $FrameworkContext['executionId']
        $document.frameworkContext = Copy-EvaxisJson $FrameworkContext
    }
    if ($null -ne $RunRegistry -and -not $RunRegistry.Add(
        (ConvertTo-Json -InputObject @($Collector['authority'], $CollectionRunId) -Compress)
    )) { throw 'EVX: duplicate collection run identity in the caller-owned registry.' }
    return @{
        Marker = 'evaxis.capture-session/0.1'
        OwnerRunspace = [runspace]::DefaultRunspace.InstanceId
        Document = $document; TargetKeys = $keys
    }
}

function Start-EvaxisSourceAttempt {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [hashtable] $Session,
        [Parameter(Mandatory)] [string] $AttemptId,
        [Parameter(Mandatory)] [AllowEmptyCollection()] [object[]] $IntendedTargets
    )
    Assert-EvaxisSession $Session
    Assert-EvaxisIdentifier $AttemptId
    if (@($Session.Document.sourceAttempts | Where-Object { $_.attemptId -ceq $AttemptId }).Count) {
        throw 'EVX: duplicate source attempt identifier.'
    }
    $keys = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $targets = @()
    foreach ($target in $IntendedTargets) {
        $key = Assert-EvaxisDeclaredTarget $Session $target
        if (-not $keys.Add($key)) { throw 'EVX: duplicate intended target identity.' }
        $targets += ,(Get-EvaxisTargetReference $target)
    }
    $Session.Document.sourceAttempts += ,[ordered]@{
        attemptId = $AttemptId; collectionRunId = $Session.Document.collectionRunId
        intendedScope = Copy-EvaxisJson $Session.Document.requestedScope
        intendedTargets = $targets; startedAt = Get-EvaxisNow; status = 'in-progress'
    }
}

function Add-EvaxisObservation {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [hashtable] $Session,
        [Parameter(Mandatory)] [string] $AttemptId,
        [Parameter(Mandatory)] [string] $ObservationId,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Target,
        [Parameter(Mandatory)] [string] $ObservedAt,
        [Parameter(Mandatory)] [string] $TimestampOrigin,
        [Parameter(Mandatory)] [string] $ClockBasis,
        [Parameter(Mandatory)] [string] $ObservationType,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $ObservationSchema,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Representation,
        [string] $CollectionRunId,
        [AllowEmptyCollection()] [object[]] $Transformations = @()
    )
    Assert-EvaxisSession $Session
    if ($CollectionRunId -and $CollectionRunId -cne $Session.Document.collectionRunId) {
        throw 'EVX: observation cannot be attached to another run.'
    }
    $attempt = Get-EvaxisAttempt $Session $AttemptId
    $key = Assert-EvaxisDeclaredTarget $Session $Target
    if (-not @($attempt.intendedTargets | Where-Object { (Get-EvaxisTargetKey $_) -ceq $key }).Count) {
        throw 'EVX: observation target is unrelated to the source attempt.'
    }
    Assert-EvaxisIdentifier $ObservationId
    Assert-EvaxisIdentifier $ObservationType
    foreach ($name in 'id', 'version') { Assert-EvaxisIdentifier $ObservationSchema[$name] }
    $null = Assert-EvaxisTime $ObservedAt
    if ($TimestampOrigin -cnotin @('source-reported', 'collector-observed', 'synthetic-fixture', 'caller-supplied') -or
        [string]::IsNullOrWhiteSpace($ClockBasis)) { throw 'EVX: source timestamp provenance is required.' }
    if (-not $Target.Contains('kind') -or -not $Target.Contains('lifecycle')) {
        throw 'EVX: explicit object kind and lifecycle basis are required.'
    }
    Assert-EvaxisIdentifier $Target['kind']
    if ($Target['lifecycle'] -isnot [System.Collections.IDictionary] -or
        $Target['lifecycle']['state'] -cnotin @('active', 'deletion-confirmed', 'unknown') -or
        $Target['lifecycle']['basis'] -cnotin @('direct-observation', 'source-tombstone', 'collector-inference', 'unknown')) {
        throw 'EVX: target lifecycle state and basis are invalid.'
    }
    if ($Target['lifecycle']['state'] -ceq 'deletion-confirmed') {
        Assert-EvaxisIdentifier $Target['lifecycle']['evidenceReference']
        if ($Target['lifecycle']['basis'] -cnotin @('direct-observation', 'source-tombstone')) {
            throw 'EVX: deletion requires positive source-attributable lifecycle evidence.'
        }
    }
    if ($Representation.Contains('content') -eq $Representation.Contains('reference') -or
        $Representation['encoding'] -cnotin @('source-native', 'json', 'text', 'opaque-reference', 'other')) {
        throw 'EVX: representation requires one content or reference and an explicit encoding.'
    }
    if ($Representation.Contains('reference')) { Assert-EvaxisIdentifier $Representation['reference'] }
    if (@($Session.Document.observations | Where-Object { $_.record.observationId -ceq $ObservationId }).Count) {
        throw 'EVX: duplicate observation identifier.'
    }
    if (@($Session.Document.notObserved | Where-Object { (Get-EvaxisTargetKey $_.target) -ceq $key }).Count) {
        throw 'EVX: target is already declared not observed.'
    }
    $item = [ordered]@{
        record = [ordered]@{
            observationId = $ObservationId; contractVersion = '0.1'
            collectionRunId = $Session.Document.collectionRunId; observedAt = $ObservedAt
            source = Copy-EvaxisJson $Session.Document.source; target = Copy-EvaxisJson $Target
            observationType = $ObservationType; observationSchema = Copy-EvaxisJson $ObservationSchema
            collector = Copy-EvaxisJson $Session.Document.collector
            representation = Copy-EvaxisJson $Representation
        }
        attemptId = $AttemptId; capturedAt = Get-EvaxisNow
        observedAtProvenance = [ordered]@{ origin = $TimestampOrigin; clockBasis = $ClockBasis }
        transformations = Copy-EvaxisJson $Transformations
    }
    $Session.Document.observations += ,$item
}

function Complete-EvaxisSourceAttempt {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [hashtable] $Session,
        [Parameter(Mandatory)] [string] $AttemptId,
        [Parameter(Mandatory)] [string] $Status,
        [System.Collections.IDictionary] $Limitation,
        [AllowEmptyCollection()] [object[]] $VisibilityConstraints = @()
    )
    Assert-EvaxisSession $Session
    $attempt = Get-EvaxisAttempt $Session $AttemptId
    if ($Status -cnotin @('succeeded', 'failed', 'unsupported', 'unavailable', 'denied', 'malformed', 'not-attempted')) {
        throw 'EVX: unsupported source attempt state.'
    }
    $items = @($Session.Document.observations | Where-Object { $_.attemptId -ceq $AttemptId })
    $observed = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($item in $items) { $null = $observed.Add((Get-EvaxisTargetKey $item.record.target)) }
    if ($Status -ceq 'succeeded' -and $observed.Count -ne $attempt.intendedTargets.Count) {
        throw 'EVX: successful attempt must observe every intended target.'
    }
    if ($Status -cin @('denied', 'unavailable', 'unsupported', 'not-attempted') -and $items.Count) {
        throw 'EVX: non-collecting attempt cannot contain observations.'
    }
    if ($Status -cne 'succeeded' -and (-not $Limitation -or
        [string]::IsNullOrWhiteSpace($Limitation['description']))) {
        throw 'EVX: non-success attempt requires a minimized limitation.'
    }
    $limitationCopy = if ($Limitation) { Copy-EvaxisJson $Limitation } else { $null }
    if ($limitationCopy) { Assert-EvaxisIdentifier $limitationCopy['code'] }
    $constraintsCopy = Copy-EvaxisJson $VisibilityConstraints
    if ($limitationCopy) { $attempt.limitation = $limitationCopy }
    if ($constraintsCopy.Count) { $attempt.visibilityConstraints = $constraintsCopy }
    $attempt.completedAt = Get-EvaxisNow
    $attempt.status = $Status
}

function Add-EvaxisNotObservedTarget {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [hashtable] $Session,
        [Parameter(Mandatory)] [string] $AttemptId,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Target,
        [Parameter(Mandatory)] [string] $Reason
    )
    Assert-EvaxisSession $Session
    $attempt = Get-EvaxisAttempt $Session $AttemptId -AllowCompleted
    $key = Assert-EvaxisDeclaredTarget $Session $Target
    if ($attempt.status -cin @('in-progress', 'succeeded') -or
        $Reason -cnotin @('denied', 'unavailable', 'unsupported', 'not-attempted', 'unknown') -or
        ($Reason -cne 'unknown' -and $Reason -cne $attempt.status)) {
        throw 'EVX: non-observation reason requires a matching completed source attempt.'
    }
    if (-not @($attempt.intendedTargets | Where-Object { (Get-EvaxisTargetKey $_) -ceq $key }).Count) {
        throw 'EVX: not-observed target is unrelated to the source attempt.'
    }
    if (@($Session.Document.observations | Where-Object { (Get-EvaxisTargetKey $_.record.target) -ceq $key }).Count -or
        @($Session.Document.notObserved | Where-Object { (Get-EvaxisTargetKey $_.target) -ceq $key }).Count) {
        throw 'EVX: target is already observed or declared not observed.'
    }
    $Session.Document.notObserved += ,[ordered]@{
        target = Get-EvaxisTargetReference $Target; reason = $Reason
        attemptId = $AttemptId; recordedAt = Get-EvaxisNow
    }
}

function Add-EvaxisAssessment {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [hashtable] $Session,
        [Parameter(Mandatory)] [string] $AssessmentId,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Subject,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Rule,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $Evaluator,
        [Parameter(Mandatory)] [string] $AssessedAt,
        [Parameter(Mandatory)] [string] $TimestampOrigin,
        [Parameter(Mandatory)] [string] $ClockBasis,
        [Parameter(Mandatory)] [string] $ExecutionStatus,
        [Parameter(Mandatory)] [string] $Outcome,
        [Parameter(Mandatory)] [AllowEmptyCollection()] [string[]] $ObservationReferences,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $InputBasis,
        [Parameter(Mandatory)] [System.Collections.IDictionary] $ControlCoverage,
        [System.Collections.IDictionary] $FrameworkAssociation
    )
    Assert-EvaxisSession $Session
    $subjectKey = Assert-EvaxisDeclaredTarget $Session $Subject
    Assert-EvaxisIdentifier $AssessmentId
    Assert-EvaxisVersionedIdentity $Rule
    Assert-EvaxisVersionedIdentity $Evaluator
    $assessedTime = Assert-EvaxisTime $AssessedAt
    if ($assessedTime -gt [DateTimeOffset]::UtcNow -or
        $TimestampOrigin -cnotin @('evaluator-event', 'framework-event', 'caller-supplied') -or
        [string]::IsNullOrWhiteSpace($ClockBasis)) { throw 'EVX: assessment timestamp provenance is invalid.' }
    if ($ExecutionStatus -cnotin @('completed', 'failed', 'unsupported', 'not-run') -or
        $Outcome -cnotin @('pass', 'fail', 'unknown') -or
        ($ExecutionStatus -cne 'completed' -and $Outcome -cne 'unknown')) {
        throw 'EVX: assessment execution status and outcome contradict.'
    }
    if (@($Session.Document.assessments | Where-Object { $_.record.assessmentId -ceq $AssessmentId }).Count) {
        throw 'EVX: duplicate assessment identifier.'
    }
    $refs = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $hasSubject = $false
    foreach ($reference in $ObservationReferences) {
        Assert-EvaxisIdentifier $reference
        $matches = @($Session.Document.observations | Where-Object { $_.record.observationId -ceq $reference })
        if ($matches.Count -ne 1 -or -not $refs.Add($reference)) {
            throw 'EVX: assessment observation reference is duplicate or unresolved.'
        }
        if ((Get-EvaxisTargetKey $matches[0].record.target) -ceq $subjectKey) { $hasSubject = $true }
    }
    $basisKind = $InputBasis['kind']
    if ($basisKind -cnotin @('observations', 'declared-scope', 'external-references', 'no-input') -or
        [string]::IsNullOrWhiteSpace($InputBasis['rationale']) -or
        ($basisKind -ceq 'observations' -and -not $hasSubject) -or
        ($basisKind -ceq 'external-references' -and (-not $InputBasis.Contains('externalReferences') -or
            $InputBasis['externalReferences'].Count -eq 0))) {
        throw 'EVX: assessment lacks legitimate input basis or subject-matching evidence.'
    }
    $assessed = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    $unassessed = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    if ($ControlCoverage['status'] -cnotin @('complete', 'partial', 'unknown') -or
        $ControlCoverage['assessedSubjects'] -isnot [array] -or
        $ControlCoverage['unassessedSubjects'] -isnot [array]) {
        throw 'EVX: explicit control coverage state and subject arrays are required.'
    }
    foreach ($target in $ControlCoverage['assessedSubjects']) {
        if (-not $assessed.Add((Assert-EvaxisDeclaredTarget $Session $target))) {
            throw 'EVX: duplicate assessed subject.'
        }
    }
    foreach ($item in $ControlCoverage['unassessedSubjects']) {
        if (-not $unassessed.Add((Assert-EvaxisDeclaredTarget $Session $item.target))) {
            throw 'EVX: duplicate unassessed subject.'
        }
    }
    if ($assessed.Overlaps($unassessed) -or
        ($ControlCoverage['status'] -ceq 'complete' -and $unassessed.Count) -or
        ($Outcome -cin @('pass', 'fail') -and (
            $basisKind -ceq 'no-input' -or $ControlCoverage['status'] -ceq 'unknown' -or
            -not $assessed.Contains($subjectKey)
        ))) { throw 'EVX: assessment conclusion contradicts input or control coverage.' }
    if ($null -ne $FrameworkAssociation) {
        if (-not $Session.Document.Contains('frameworkContext') -or
            $FrameworkAssociation['executionId'] -cne $Session.Document.frameworkContext.executionId -or
            $FrameworkAssociation['collectionRunId'] -cne $Session.Document.collectionRunId) {
            throw 'EVX: framework sidecar belongs to another run or execution.'
        }
    }
    $item = [ordered]@{
        record = [ordered]@{
            assessmentId = $AssessmentId; contractVersion = '0.1'
            subject = Copy-EvaxisJson $Subject; rule = Copy-EvaxisJson $Rule
            evaluator = Copy-EvaxisJson $Evaluator; assessedAt = $AssessedAt
            executionStatus = $ExecutionStatus; outcome = $Outcome
            observationReferences = Copy-EvaxisJson $ObservationReferences
            inputBasis = Copy-EvaxisJson $InputBasis
            controlCoverage = Copy-EvaxisJson $ControlCoverage
            freshness = [ordered]@{ status = 'unknown' }
        }
        collectionRunId = $Session.Document.collectionRunId; recordedAt = Get-EvaxisNow
        assessedAtProvenance = [ordered]@{ origin = $TimestampOrigin; clockBasis = $ClockBasis }
    }
    if ($null -ne $FrameworkAssociation) { $item.frameworkAssociation = Copy-EvaxisJson $FrameworkAssociation }
    $Session.Document.assessments += ,$item
}

function Complete-EvaxisCapture {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [hashtable] $Session,
        [Parameter(Mandatory)] [string] $CollectionStatus,
        [Parameter(Mandatory)] [string] $CoverageStatus
    )
    Assert-EvaxisSession $Session
    if ($CollectionStatus -cnotin @('succeeded', 'partial', 'failed', 'unsupported', 'unavailable', 'denied', 'malformed', 'not-attempted') -or
        $CoverageStatus -cnotin @('complete', 'partial', 'unknown')) { throw 'EVX: unsupported collection or coverage state.' }
    $attempts = $Session.Document.sourceAttempts
    if (-not $attempts.Count -or @($attempts | Where-Object { $_.status -ceq 'in-progress' }).Count) {
        throw 'EVX: collection cannot complete with missing or unresolved source attempts.'
    }
    $observed = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($item in $Session.Document.observations) { $null = $observed.Add((Get-EvaxisTargetKey $item.record.target)) }
    $accounted = [System.Collections.Generic.HashSet[string]]::new($observed, [StringComparer]::Ordinal)
    foreach ($item in $Session.Document.notObserved) {
        if (-not $accounted.Add((Get-EvaxisTargetKey $item.target))) { throw 'EVX: coverage target sets overlap or duplicate.' }
    }
    if (($Session.Document.inventory.status -ceq 'unknown' -and $CoverageStatus -cne 'unknown') -or
        ($CoverageStatus -ceq 'complete' -and -not $observed.SetEquals($Session.TargetKeys)) -or
        ($CoverageStatus -ceq 'partial' -and -not $accounted.SetEquals($Session.TargetKeys))) {
        throw 'EVX: coverage contradicts the declared candidate inventory.'
    }
    if ($CollectionStatus -ceq 'succeeded' -and ($CoverageStatus -cne 'complete' -or
        @($attempts | Where-Object { $_.status -cne 'succeeded' }).Count)) {
        throw 'EVX: successful collection cannot contain failed or incomplete attempts.'
    }
    if ($CollectionStatus -cnotin @('succeeded', 'partial') -and ($observed.Count -or
        @($attempts | Where-Object { $_.status -cne $CollectionStatus }).Count)) {
        throw 'EVX: collection health contradicts source attempts or observations.'
    }
    $Session.Document.collectionStatus = $CollectionStatus
    $Session.Document.coverageStatus = $CoverageStatus
    $Session.Document.completedAt = Get-EvaxisNow
    $Session.Document.state = 'completed'
}

function Get-EvaxisCaptureDocument {
    [CmdletBinding()]
    param([Parameter(Mandatory)] [hashtable] $Session)
    Assert-EvaxisSession $Session -AllowCompleted
    if ($Session.Document.state -cne 'completed') { throw 'EVX: only completed capture documents can be exported.' }
    return Copy-EvaxisJson $Session.Document
}

function Export-EvaxisCapture {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)] [hashtable] $Session,
        [Parameter(Mandatory)] [string] $OutputDirectory,
        [string] $PythonCommand = 'python'
    )
    $document = Get-EvaxisCaptureDocument $Session
    $json = ConvertTo-Json -InputObject $document -Depth 40 -Compress -WarningAction Stop
    if ([Text.Encoding]::UTF8.GetByteCount($json) -gt 1000000) { throw 'EVX: capture exceeds the 1 MB limit.' }
    $command = Get-Command $PythonCommand -CommandType Application -ErrorAction SilentlyContinue
    if (-not $command) { throw 'EVX: Python and the pinned validation dependency are required for export.' }
    $assembly = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\capture\package.py'))
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $command.Source
    foreach ($argument in @($assembly, 'assemble', '--stdin', '--output', $OutputDirectory)) { $start.ArgumentList.Add($argument) }
    $start.UseShellExecute = $false
    $start.RedirectStandardInput = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.StandardInputEncoding = [Text.UTF8Encoding]::new($false)
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $start
    try {
        if (-not $process.Start()) { throw 'EVX: could not start package validation.' }
        $outputTask = $process.StandardOutput.ReadToEndAsync()
        $errorTask = $process.StandardError.ReadToEndAsync()
        $process.StandardInput.Write($json)
        $process.StandardInput.Close()
        if (-not $process.WaitForExit(120000)) {
            $process.Kill($true)
            throw 'EVX: bounded package validation timed out; no completed output is claimed.'
        }
        $output = $outputTask.GetAwaiter().GetResult()
        $errorText = $errorTask.GetAwaiter().GetResult()
        if ($process.ExitCode -ne 0) {
            if ($errorText.StartsWith('evidence operation failed:')) { throw ('EVX: ' + $errorText.Trim()) }
            throw 'EVX: package validation or assembly failed; no output was finalized.'
        }
        $validation = ConvertFrom-Json -InputObject $output -AsHashtable -ErrorAction Stop
        return [pscustomobject]@{
            CollectionRunId = $document.collectionRunId
            OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
            Validation = $validation
        }
    }
    finally { $process.Dispose() }
}
