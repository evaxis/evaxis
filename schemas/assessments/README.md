# Assessment-result schema

`assessment-result-v0.1.schema.json` is a proposed Draft 2020-12 structural
schema for rule/evaluator identity and versions, referenced observations,
assessment time, execution status, outcome, freshness and control coverage.
The [architecture specification](https://github.com/evaxis/architecture/blob/main/specifications/evidence-envelope-v0.1.md)
owns the meaning and separation of these fields. A schema-valid result is not
proof that an assessment ran correctly or that its collection was complete.
Completed Pass/Fail outcomes declare an explicit input basis and cannot claim
unknown control coverage. Package validation separately resolves observation
references. Pending review; no evaluator is implemented.
