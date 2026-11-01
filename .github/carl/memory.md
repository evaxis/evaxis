# Evaxis core governance memory

## Confirmed purpose and stage

Evaxis (EVidence + AXIS): Evidence Across Every Axis.
This repository is the future home of the independent, provider-neutral security
evidence, provenance, historical analysis and assurance core. It is in the
foundation/design stage, not an implemented product. A separately authorized
synthetic preservation experiment now captures source facts and validates a
complete package; no provider-connected collection, storage, assessment,
drift, authentication, hosting or billing service exists here.

The canonical logo is the existing organisation avatar:
https://avatars.githubusercontent.com/u/349042465?v=4
Reference this URL; do not generate or commit replacement artwork.

## Repository map

- `docs/getting-started.md`: design-stage orientation, not product installation.
- `docs/evidence-preservation.md`: reproducible experimental capture/helper,
  local assembly, optional pinned native execution, and supported boundaries.
- `capture/`: separate capture `0.1` data schema and prototype Python assembly/
  validation; not a new normative Envelope contract or product stack choice.
- `integrations/powershell/`: replaceable explicit-session helper, independent
  of Maester; `integrations/maester/` holds narrowly scoped synthetic glue.
- `examples/evidence-preservation/` and `tests/capture/`: genuinely generated
  golden package and executable positive/adversarial/behavioral tests.
- `schemas/{evidence,observations,assessments,manifests}/`: proposed modular
  Evidence Envelope v0.1 schemas; the architecture repository's
  `specifications/evidence-envelope-v0.1.md` owns human semantics, while this
  repository owns schema structure.
- `examples/{complete-assessment,incomplete-collection,environment-drift,evaluator-drift}/`:
  reserved scenario directories, without findings or example data.
- `tests/conformance/`: synthetic schema fixtures and machine-readable
  semantic expectations; validation checks individual shape and the linked
  packages' reference/coverage consistency, not comparison behavior. Producer
  verification/authentication fields remain claims until a separate receiver-
  owned verification record exists.
- `https://github.com/evaxis/architecture`: architectural records and roadmap.
- `https://github.com/evaxis/.github`: shared community governance and profile.

## Security and engineering invariants

These are repository-specific canonical invariants, supplementing the bundled
`.github/carl/invariants.yml`; none relax the bundled policy.

1. Core independence: Evaxis must remain independent of Maester, Microsoft,
   Netlify, Cloudflare, Azure and every other individual technology provider.
2. Execution independence: assessment and comparison logic must not require
   one fixed execution environment. Customer-controlled runners, hosted or
   hybrid processing and future Maester Cloud runners remain potential options.
3. Storage portability: interchangeable storage must remain possible, including
   local and customer-managed storage. No backend has been selected.
4. Cryptographic flexibility: preserve client-side, server-side and hybrid
   processing options. Per-customer key isolation and envelope encryption are
   preferred directions, not implemented controls or selected algorithms.
5. Evidence integrity: design for immutable evidence, provenance, source and
   collector identity, collection timestamps, completeness, freshness and replay
   protection. Producer-supplied authentication/integrity fields are claims,
   never receiver-established trust. Do not claim these properties are already
   implemented.
6. Semantic correctness: distinguish environmental drift from schema,
   collection, identity-resolution and evaluation changes.
7. Contract ownership: architecture owns Evidence Envelope terminology,
   semantics, lifecycle, threat limits and compatibility decisions; this
   repository owns versioned machine-readable schemas and synthetic fixtures.
   Keep both aligned on explicit contract version `0.1`; do not duplicate or
   silently redefine normative meanings here.
8. Commercial independence: useful baseline functionality should remain
   accessible without a hosted paid service. Premium entitlements must not
   become inseparably coupled to a storage provider.
9. Maester separation: Maester Packs and Maester Cloud Plugins are proposed
   integrations, not execution or storage foundations. Their provider APIs,
   structured evidence storage, licensing and revenue sharing are not contracts.
10. No speculative commitments: do not select implementation languages, build
   systems, databases, clouds, cryptographic algorithms or commercial terms.
   Mark claims Confirmed, Proposed or Undecided.
11. Licensing is undecided. Public visibility is not an open-source licence.
    No root LICENSE or substantial product implementation before approval.
    The explicitly authorized bounded synthetic helper/proof does not select
    product licensing/stack or waive future implementation approval.
    Upstream cARL retains its own licence in `THIRD_PARTY_NOTICES.md`.
12. No secrets, customer evidence, tenant identifiers or sensitive findings in
    public files, issues, fixtures, logs or pull requests.
13. Use pull requests after the initial bootstrap. Never bypass reviews, enable
    auto-merge, force-push, delete protected branches or weaken protections to
    make automation succeed. Never modify unrelated organisations or projects.

## Source-verified Maester compatibility research

`docs/maester-compatibility.md` records the pinned Maester 3.0.0 result
boundary and points to Architecture's research/ADR. Native Maester statuses
are execution and producer assessment claims, not source observations; normal
rows lack enough run, subject, collection and source provenance to populate a
complete v0.1 package without invention. There is no generic Core result importer
or change to the four Envelope schemas. The separately authorized preservation
prototype instead captures facts inside the actual synthetic native callback.
Keep integrations optional and outside provider-neutral schemas; reject
incomplete mappings rather than fabricate evidence. The v0.1
specification and schemas are merged into their default branches, but the
authoritative specification remains explicitly proposed pending maintainer
review and architectural approval. The tracked offline-only verification
tool is in `tools/maester-lab/`; it fetches exact commits, runs reviewed
synthetic demo cases and keeps raw output outside the checkout. It is not an
adapter or provider-connected compatibility test.

## Experimental preservation boundary

Capture `0.1` is provider-neutral JSON referencing the existing proposed
Envelope `0.1` records. The distinct preservation architecture/ADR proposal is
in https://github.com/evaxis/architecture/pull/5; neither it, ADR 0002, nor the
Envelope specification is promoted to approval by this prototype.
API/coverage/assessment choices remain reviewable proposals.

One capture run has one source authority/scope; one package has one envelope/
manifest and zero-or-more observations/assessments. Target identity is the
case-sensitive authority/scope/native-ID tuple. Unknown inventory retains only
declared candidates and coverage remains unknown; display names and native test
suffixes do not establish identity or completeness.

The PowerShell helper owns explicit collecting/completed and attempt states.
Completion is non-idempotent; a session is single-writer and runspace-owned.
Caller-owned optional run registries are not durable replay protection.
Source timestamp strings and clock assumptions remain separate from actual
capture/attempt/run/assessment-recording UTC events. JSON values are copied
defensively; unsupported numeric precision fails instead of being lost.

The prototype assembler preserves richer lineage in reserved
`evaxis.capture/0.1`, validates unchanged schemas and package/lineage invariants,
and publishes two JSON files through private staging and no-replace atomic
local finalization. The separately authorized portable follow-up adds pinned
Windows ancestor handles and descriptor-relative Linux input/staging/writes/
rename/cleanup, regular-file checks and explicit unsupported-path/primitive
failures. Windows directory pinning uses read access without delete sharing:
metadata-only handles did not prevent ancestor rename in real regression
execution. Actual Windows Server 2025/Ubuntu 24.04 x64 CI passed with Python
3.11/3.13, including native capture and Linux's real no-replace syscall;
[measured configurations](../../docs/evidence-preservation.md) qualify only
those tested images/runtimes/filesystem observations. macOS publication remains
unsupported.
Selected replacement races are mitigated, not arbitrary privileged/same-
identity attackers, hostile mounts, network filesystems, crash durability,
immutable storage, cryptographic verification, global deduplication or receiver
trust. A detected post-rename parent change may leave a complete bundle in the
original parent but never reports completion or deletes that destination.

Optional native glue uses a one-use caller-runspace registry, explicit scalar
run/execution/invocation parameters and matching emitted native `Parameters`.
Those tokens are wrapper-created, not upstream Maester run IDs or attestation.
The genuine native proof captures two synthetic source facts before evaluation
and records Passed, Failed and unavailable Skipped as distinct assessment/
collection outcomes. It is not a Pack, generic importer or tenant test.

Use `python tools\validate_conformance.py`,
`python -B -m unittest discover -s tests\capture -p 'test_*.py' -q`, and
`pwsh -NoProfile -File tests\capture\Test-Capture.ps1`.
The optional local native integration test requires the exact source/module
pins and `EVAXIS_MAESTER_SOURCE`; otherwise its skip is explicit.
`tools/ci/` instead reuses hash-locked Python wheels, checksum-verified existing
Maester/Graph prerequisites and a runner requiring actual native execution.
The separate capture workflow targets x64 Windows Server 2025/Ubuntu 24.04 and
Python 3.11/3.13, using read-only permissions, no secrets and fresh runners.
Native Maester 3.0.0 and the standalone PowerShell suite need no Pester
dependency. CI configuration is not execution evidence; preserve measured
results and explicit platform skips. Runtime scripts never install modules or
upload evidence. See developer docs for prerequisites and trust limitations.
The final-code [four-job run](https://github.com/evaxis/evaxis/actions/runs/41337237522)
executed 121 Python cases on each Windows job and 126 on each Linux job out of
130 discovered, with only opposite-platform skips. Every job passed conformance,
36 PowerShell cases and the required native two-observation/three-assessment
proof. Native Failed/Skipped assessment outcomes are not suite skips.
The initial real Linux execution exposed a non-regular descriptor reaching
`fdopen`; validation and close now precede stream construction rather than
relaxing the expected failure semantics.

Publication/integrity errors remain primary when staging or retained-handle
cleanup also fails. Safe secondary cleanup diagnostics are Python 3.11
exception notes, separately printed by the CLI; cleanup-only errors still
fail, and no published destination is removed to conceal uncertainty.
The final review adds `Capture validation gate`, an always-run aggregate
requiring a successful matrix dependency and the exact four fresh mandatory-
native reports. Ordinary GitHub required checks accept skipped/neutral
conclusions; require the aggregate as well as cARL and all four matrix names.
Keep strict/PR-only/no-bypass/zero-approval rules unchanged and review workflow
changes: required statuses do not authenticate contributor-controlled job code.
See [merge-gate configuration](../../tools/ci/README.md#merge-gate).

## Repository-specific trust boundaries

These supplement `.github/carl/trust-boundaries.md`.

| Crossing | Required control |
|---|---|
| External contribution into contracts | Treat PR/issue text and attachments as untrusted; require explicit approved scope and maintainer review. |
| Canonical policy into harness context | `.github/carl/` and effective packs are authoritative; generated loaders are not competing instructions or proof of adherence. |
| GitHub token into administration | Verify owner, target and actual remote settings; least privilege; no self-administration workflow or stored administration token. |
| PR content into CI | Read-only token, no secrets, no `pull_request_target`, no privileged execution of contributor code. |
| Sensitive report into public discussion | Use private vulnerability reporting; never publish customer evidence or credentials. |
| Future source/collector into evidence | Define identity, provenance, timestamps, completeness, freshness and replay validation before accepting trust claims. |
| Future evidence into evaluator/comparison | Preserve schema, collection, identity-resolution and evaluator context; incomplete collection must not imply compliance or environmental drift. |
| Architecture semantics into core schema | Treat architecture as the sole human-semantic authority and core schemas/fixtures as machine-readable structure/expectations; align explicit contract versions and review changes in both repositories. |
| Future tenant into storage/key/execution context | Specify authorization, per-customer isolation and key ownership; interchangeable adapters must not erase trust assumptions. |
| Future Maester integration into core | Keep provider APIs and entitlements outside independent evidence and comparison contracts; no implicit trust from publisher identity. |

## cARL ownership and workflow

cARL 1.0.2 is pinned by `runtime.json`. Preserve bundled managed invariants,
trust-boundary guidance, templates, packs and adapters byte-for-byte; repository
decisions live in this protected, repository-owned memory and human-facing docs.
This avoids concealing intentional local policy as unmanaged runtime drift.
Do not run `carl repair` to erase repository decisions.

`packs.json` selects nine `core/*` governance packs and `platform/cicd`.
`profiles.json` activates the `foundations` profile. Bundled cloud, language,
Docker and Kubernetes files are inactive reference assets, not stack decisions.
Use supported `carl pack select`, `unselect` and `profile activate` commands.

Before each change, hydrate cARL, replace the current PR contract with the new
approved scope, identify acceptance checks and stop conditions, and reconcile
durable decisions before closing the contract. A completed bootstrap contract
does not authorise later implementation.

Run `carl doctor`, `carl status`, `carl pack effective`, `carl trace` and
`carl harness status` with the pinned CLI. The workflow verifies the downloaded
release checksum. These diagnostics do not prove native harness adherence.
JFrog Boost must exclude `.github/carl/**` from optimisation.
Local diagnostics retained 42 pre-existing warnings and five drifted harness
adapters. Their cause remains unverified; the portable work did not repair
shared managed assets or treat successful CI as permission to repair them.

## Proposed next milestone and open decisions

Next: review and explicitly approve the proposed Evaxis Evidence Envelope v0.1,
the distinct preservation proposal and its experimental machine contract/
helper. Validation now includes executable capture/assembly behavior, but is
not a comparison engine and does not verify compact semantic expectations,
source truth or receiver trust.
Licensing, contribution rights, execution model, storage adapters, identity,
cryptographic design, commercial entitlements and all provider contracts remain
undecided. No partnerships, affiliations or endorsements are established.
