# Synthetic evidence-preservation rule

Experimental, credential-free native test for the pinned Maester 3.0.0 engine.
The orchestrator supplies opaque run, execution, and one-use invocation IDs.
The registered context identifies the synthetic source-native target explicitly;
it is never inferred from a test ID suffix, filename, or display name.

Source collection and preservation happen inside the native test before the
framework creates its normal result row. The rule evaluates only the captured
`enabled` boolean. Available true and false values produce Passed and Failed;
an explicitly unavailable source produces Skipped and an unknown Evaxis
assessment with no fabricated observation.

The normal row is not evidence. The orchestrator checks its outcome against the
execution-associated capture and then finalizes the independent package.
Run only through [`Invoke-SyntheticMaester.ps1`](Invoke-SyntheticMaester.ps1).
This is not a published Pack, provider collector, or approved assurance rule.

<!--- Results --->
%TestResult%
