# Maester compatibility review remediation

## Contract status

Closed — final documentation correction committed to
[Core PR #2](https://github.com/evaxis/evaxis/pull/2) on
`feat/maester-adapter`; the PR remains open and unmerged. The change only
corrects the documented PowerShell parameter for projection comparison.

## Goal and approved scope

Correct `docs/maester-compatibility.md` to state that projection comparison is
enabled by default and `-SkipProjection` disables it, matching
`tools/maester-lab/verify-maester.ps1`.

## Non-goals and forbidden scope

Do not modify the verification script, fixtures, schemas, ADRs, Architecture
PR #4, or unrelated files. No adapter, tenant testing, Pack
installation/publication, merge, or other implementation/architecture change.

## Expected files

- `.github/carl/current-pr-contract.md`
- `docs/maester-compatibility.md`
- `.github/carl/plans/maester-adapter.md`

## Contract assertions and validation

1. The incorrect projection-path option reference is removed from Core
   compatibility documentation.
2. The documented default comparison and `-SkipProjection` behavior match the
   tracked script's `param` declaration and control flow.
3. No script, fixture, schema, ADR, Architecture file, or unrelated
   documentation changes.

Search documentation for stale parameter references, verify Markdown links,
run `git diff --check` and applicable cARL/GitHub checks. Do not rerun Maester.

## Trust boundaries and stop conditions

This documentation-only change does not authorize or require running the
Maester tool. Stop if correcting the text requires changing its implementation
or any file outside the narrow approved scope.

## Reconciliation

This correction clarifies an existing script interface; no new durable
project behavior or memory change is required.
