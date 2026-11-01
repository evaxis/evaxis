# Evidence Envelope v0.1 conformance proposal

The [architecture proposal](https://github.com/evaxis/architecture/blob/main/specifications/evidence-envelope-v0.1.md)
owns normative semantics. Conformance data is split into four layers:

1. `fixtures/schema-valid/` and `fixtures/schema-invalid/` contain complete
   individual records for structural validation, including a positive explicit
   JSON-null representation case, an explicit declared-scope assessment basis,
   and negative conflicting content/reference and `claims-verified` without
   `verificationClaim` cases. Invalid examples are expected rejections. The
   validator also checks that a valid `claims-verified` claim with metadata
   passes and other permitted claim statuses do not require that metadata.
2. Those valid records form one linked synthetic package; package checks resolve
   envelope and assessment references, verify run membership, and enforce
   coverage/source-attempt consistency, target uniqueness, partitioning and
   set membership. `packageConsistencyCases` includes
   deliberately invalid mutations whose rejection is required.
3. `cases.json` semantic expectations contain compact scenario facts,
   per-dimension outcomes and declared preconditions. Environmental conclusions
   stipulate a receiver-verification premise; this is not performed by the
   validator. They are **not** complete schema-valid package vectors and are
   not executed by a comparison engine.
4. [`tests/capture/`](../capture/README.md) separately executes capture,
   multi-record assembly, lifecycle, privacy and synthetic native integration
   behavior. Comparison behavior remains deferred until an independently
   reviewed comparison implementation exists.

Run locally with Python 3.11 or later and the pinned validation-only dependency:

```sh
python3 -m pip install -r requirements-dev.txt
python3 tools/validate_conformance.py
```

The validator checks JSON parsing, dependency-independent date-time formats,
Draft 2020-12 schema structure, individual
fixture validity/expected rejection, the one linked package's references and
coverage invariants, package-level invalid mutations, unique case IDs,
version/compatibility metadata, semantic precondition/result presence, local
documentation links, whitespace and common credential patterns. It does
**not** execute or verify semantic expected outcomes, perform evidence
comparison, verify digests/signatures, or establish source truth, freshness or
whole-environment completeness. The package-consistency function also accepts arrays of observations and
assessments while retaining the original singular-fixture call interface.
It resolves exact record inventories, collector/run/source/subject membership
and control coverage; it is not tied to the old fixture's counts or IDs.
The [new assembly CLI](../../capture/README.md) validates independently assembled
packages with one envelope/manifest and zero-or-more observations/assessments.
The compact semantic cases remain
specification expectations, not executable behavioral tests.

All fixture data is synthetic and illustrative. The schema and cases are
proposals pending architectural/maintainer review, not product capabilities or
an approved assurance claim. No CI workflow or product language/runtime is
selected by this validation-only tool.
