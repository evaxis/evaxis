# Experimental capture and package assembly

Capture contract `0.1` is provider-neutral JSON, separate from the proposed
Evidence Envelope `0.1` schemas. Python is the prototype assembler/validator,
not a selected product execution foundation. It uses the existing pinned
`jsonschema` dependency and its installed `referencing` dependency; no new
package dependency is added.

Read [developer instructions](../docs/evidence-preservation.md) for the
contract, lifecycle, helper API, cardinality, privacy and unsupported behavior.
The authoritative human semantics remain in Architecture; the distinct
[preservation proposal](https://github.com/evaxis/architecture/pull/5) is not
architectural approval.

From the repository root:

```powershell
python capture\package.py validate-capture --input examples\evidence-preservation\golden\capture.json
python capture\package.py validate-package --input examples\evidence-preservation\golden\package.json
```

Assembly requires a new caller-selected destination with an existing trusted
parent and writes `capture.json` plus `package.json` atomically without
replacement. Existing Envelope schemas remain authoritative and unchanged.
Validation establishes structure/consistency only, never source truth or
receiver verification.
