@{
    RootModule = 'Evaxis.Capture.psm1'
    ModuleVersion = '0.1.0'
    GUID = 'eec88eb0-eec0-4635-b8fa-7d2f44ad16b4'
    Author = 'Evaxis'
    Description = 'Experimental provider-neutral evidence capture helper; no Maester dependency.'
    PowerShellVersion = '7.4'
    FunctionsToExport = @(
        'New-EvaxisCaptureSession',
        'Start-EvaxisSourceAttempt',
        'Add-EvaxisObservation',
        'Add-EvaxisNotObservedTarget',
        'Complete-EvaxisSourceAttempt',
        'Add-EvaxisAssessment',
        'Complete-EvaxisCapture',
        'Get-EvaxisCaptureDocument',
        'Export-EvaxisCapture'
    )
    CmdletsToExport = @()
    VariablesToExport = @()
    AliasesToExport = @()
}
