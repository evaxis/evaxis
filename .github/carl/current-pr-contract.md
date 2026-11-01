# Evidence preservation v0.1 synthetic implementation

## Contract status

Active - user-authorized implementation and pull request, without merge.
This contract explicitly supersedes the closed compatibility-remediation
contract. Core PR #2 and Architecture PR #4 are merged, verified on
2026-11-01. Latest Core `main` is
`ab0a259cb20762da312c27479286fdbd51af1be3`.

## Goal and approved scope

Implement the credential-free proof: synthetic source, reusable evidence
helper, Maester-native assessment, Evidence Envelope v0.1, and conformance
validation. The linked plan is
[evidence-preservation-v0.1.md](plans/evidence-preservation-v0.1.md).

Authorized scope includes a separate versioned provider-neutral capture
contract, replaceable PowerShell helper, package assembly, generalization of
the existing validator to multiple records, synthetic Maester glue, golden
package, positive/adversarial tests, developer documentation, and durable
repository-owned memory reconciliation. This bounded experimental
implementation is explicitly authorized; it selects no product stack,
licence, hosting service, storage backend, or approved architectural contract.

## Non-goals and forbidden scope

No changes to existing Evidence Envelope schemas, Architecture, ADR 0002,
shared cARL policy/invariants/templates/packs/adapters/runtime, CI workflows,
or unrelated repositories. No tenant connection, credentials, real evidence,
automatic evidence upload, Pack publication, release, merge, comparison
engine, receiver verification, or cryptographic assurance claims.

Evidence Envelope v0.1 remains Proposed, pending explicit architectural
approval. Architecture owns a separate proposed preservation contract/ADR.
The distinct proposal is
[evaxis/architecture#5](https://github.com/evaxis/architecture/pull/5).
Core interface choices are experimental and must remain aligned with that
proposal and the unchanged v0.1 semantic authority.

## Expected files

- `.github/carl/current-pr-contract.md`
- `.github/carl/plans/evidence-preservation-v0.1.md`
- `.github/carl/memory.md`
- `capture/`
- `integrations/powershell/`
- `integrations/maester/`
- `examples/evidence-preservation/`
- `tests/capture/`
- `tools/validate_conformance.py`
- `tests/conformance/README.md`
- `docs/evidence-preservation.md`
- `docs/maester-compatibility.md`
- `docs/getting-started.md`
- `README.md`

## Contract assertions and validation

1. Capture preserves actual run/attempt/capture events separately from
   caller-supplied source times and authority/scope/native target identity.
2. Explicit lifecycle and run associations reject duplicate identifiers,
   unresolved attempts, repeated completion, cross-run evidence, and
   contradictory collection/coverage claims.
3. Assessments preserve precise evidence references and subject, independent
   rule/evaluator versions, timing basis, execution state, conclusion, input
   basis, and control coverage; missing/denied evidence is not control Fail.
4. Assembly preserves capture lineage and produces complete multi-record
   packages validated by the unchanged v0.1 schemas and strengthened
   consistency checks; producer verification never becomes receiver trust.
5. Synthetic Maester execution captures facts before the native result loses
   them, binds the execution-associated export by explicit run identity,
   and never reconstructs source facts from verdicts or Markdown.

## Trust boundaries and stop conditions

All payloads, JSON, paths, and imported native results are untrusted. Limit
input size/depth, avoid raw evidence in diagnostics, reject traversal and
symlink/reparse paths, refuse overwrites, restrict new output permissions,
and finalize atomically in a caller-approved destination. Local files and
digests do not prove immutable storage, source truth, or independent trust.

Read-only inspection is Tier 0. Bounded code/test/docs/governance writes and
local synthetic execution are Tier 1 within this scope. The user explicitly
authorizes branch push and PR creation (Tier 2 remote mutation); never merge
or force-push. New product dependencies or semantic/schema amendments require
escalation. Reuse the pinned `jsonschema` dev dependency and the exact Maester
lab pins; install missing lab prerequisites only in a session-local location
after an actual missing-dependency failure.

Stop and report if a source interface requires a tenant, missing facts must
be fabricated, existing v0.1 invariants must be weakened, a permission
approval remains unavailable, or Architecture reports a semantic conflict.

## Reconciliation

Update developer docs and repository-owned memory for the experimental
capability, commands, supported cardinality, limitations, and unchanged
proposal status. Preserve shared managed governance byte-for-byte. Close
this contract as submitted for review after validation and PR creation;
submission does not approve architecture or authorize future work.
