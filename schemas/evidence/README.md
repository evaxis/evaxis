# Evidence envelope schema

`envelope-v0.1.schema.json` is a proposed Draft 2020-12 structural schema for
the portable package index. Its human-semantic authority is the
[Evidence Envelope v0.1 proposal](https://github.com/evaxis/architecture/blob/main/specifications/evidence-envelope-v0.1.md).
Integrity metadata is explicitly a producer claim; a receiver-established
verification result is separate and is not represented by this schema.

The envelope identifies its producer and collection run and references separate
manifest, observation and assessment records. It does not claim that a digest
proves source truth, freshness, authenticity or completeness. The schema does
not select a digest or signature algorithm. This schema is pending review and
does not imply a product implementation.
