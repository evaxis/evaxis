# Portable capture final review

## Goal and scope

Approved assisted implementation on the existing branch, starting at reviewed
head `321cbea0e059bc68c722efd8438d8eb75945b932`. Preserve portable hardening,
fix confirmed failure-provenance and execution-gate gaps, validate and open a
PR against main without merging. No Architecture, schema, dependency pin,
shared governance or trust-assurance changes.

## Hydration and findings

Current loader/canonical state and ten effective additive priority-zero
foundations packs were hydrated. Historical hardening contract is completed,
not authorization for new work; the new contract records explicit PR and
additive-ruleset permission.

F1 confirmed: effective ruleset 26000155 requires only `cARL governance`.
It is active, strict, PR-only, has no bypass actors and requires zero approvals.
GitHub accepts skipped/neutral required checks, so adding matrix names alone
does not prove successful execution. Repository-admin permission is available;
the user separately approved additive checks and the aggregate gate.
No merge queue is configured. Organisation ruleset listing lacks `admin:org`;
do not infer absent organisation policy from that permission failure.

F2 confirmed: `write_bundle` finally raises staging cleanup failure over a
publication/integrity failure; staging-descriptor/ancestor-handle close can
also mask the error or prevent later cleanup. Existing post-rename parent
uncertainty correctly retains the published bundle and must remain intact.

## Files and implementation steps

1. `capture/package.py`: retain primary exception and attach fixed safe
   Python 3.11 exception notes for secondary cleanup errors; attempt remaining
   cleanup, make cleanup-only failure explicit and show notes in CLI diagnostics.
   Keep actual rename/no-follow/handle/permission operations unchanged.
2. `tests/capture/test_capture.py`: publication failure with successful cleanup,
   primary-plus-cleanup failure, post-rename uncertainty, cleanup-only failure,
   descriptor/ancestor close provenance, sanitized CLI and clean success.
3. `.github/workflows/capture-validation.yml`, `tools/ci/check_validation_gate.py`
   and focused gate tests: always-run aggregate requires successful matrix
   dependency plus exactly four successful fresh reports and required native
   results. Artifact download adds no token permissions; pin the official
   action to verified full commit. Test failure/cancel/skip/neutral/missing
   reports, stale/malformed data and success.
4. Save live ruleset state, append the four existing matrix names plus
   `Capture validation gate` bound to GitHub Actions app 15368; preserve all
   other fields and verify effective rules. Do not test a destructive/bypass
   path against main.
5. Execute local isolated Windows and fresh four-job CI/native proof;
   reconcile direct docs, memory and contract. Push focused commits and create
   PR, then inspect its actual required checks, final CI and rule state.

## Test strategy and assertions

Tests map to the current contract's five assertions: primary diagnostic and
safe secondary notes; no uncertain success/deletion/no-overwrite regression;
fail-closed aggregate including missing execution; effective additive rules;
all supported platform/native/schema/integrity checks actually execute.
Preserve opposite-platform skips as skips, not passes.

## Risks and reconciliation

Required statuses do not make contributor-controlled workflow code tamper-proof:
maintainer review must protect the workflow/checker and its fixed four-job
configuration. No-bypass current rules still cannot prevent an administrator
from editing policy later. Cancelled workflows must not produce a successful
aggregate; missing checks block merges.
No merge queue is configured; enabling one later requires merge-group execution
and separate review. No approval deadlock is introduced.

Record real execution/required-check conclusions and residual limits in direct
docs and a saved completion report. Keep the 42 historical warnings/five
harness drifts unrepaired. Close the contract only after final verification;
do not merge or promote hostile/production suitability.
