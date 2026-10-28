# Evidence Envelope v0.1 conformance proposal

The [architecture proposal](https://github.com/evaxis/architecture/blob/main/specifications/evidence-envelope-v0.1.md)
owns normative semantics. `cases.json` contains synthetic, machine-readable
semantic scenarios and expected per-dimension outcomes. The
`fixtures/schema-valid/` and `fixtures/schema-invalid/` directories are separate
structural-validation inputs. Invalid fixtures are expected rejections and the
validator treats rejecting them as a passing negative case.

Run locally with Python 3.11 or later and the pinned validation-only dependency:

```sh
python3 -m pip install -r requirements-dev.txt
python3 tools/validate_conformance.py
```

The validator checks JSON parsing, Draft 2020-12 schema structure, fixture
validity/expected rejection, selected cross-references, unique case IDs,
version/compatibility metadata, expected-result presence, local documentation
links, whitespace and common credential patterns. It does **not** execute or
verify the semantic expected outcomes, perform evidence comparison, verify
digests/signatures, or establish source truth, freshness or collection
completeness. Those expectations require future independent behavior tests and
review.

All fixture data is synthetic and illustrative. The schema and cases are
proposals pending architectural/maintainer review, not product capabilities or
an approved assurance claim. No CI workflow or product language/runtime is
selected by this validation-only tool.
