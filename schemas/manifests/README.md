# Collection-manifest schema

`collection-manifest-v0.1.schema.json` is a proposed Draft 2020-12 structural
schema for collection run provenance, requested scope, source attempts,
visibility limits and collection coverage. Its
[architecture specification](https://github.com/evaxis/architecture/blob/main/specifications/evidence-envelope-v0.1.md)
distinguishes collection completeness from control coverage and collection
errors from assessment outcomes. A successful collection status is bounded by
its declared scope; it is not proof of whole-environment coverage. Pending
review; no collector is implemented. Package validation enforces target-set
partitioning and rejects successful runs with failed source attempts.
