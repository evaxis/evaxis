#!/usr/bin/env python3
"""Validate Evidence Envelope schema and fixture consistency, not semantics."""

from __future__ import annotations

import importlib.metadata
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator, FormatChecker, SchemaError


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "envelope": ROOT / "schemas/evidence/envelope-v0.1.schema.json",
    "manifest": ROOT / "schemas/manifests/collection-manifest-v0.1.schema.json",
    "observation": ROOT / "schemas/observations/observation-v0.1.schema.json",
    "assessment": ROOT / "schemas/assessments/assessment-result-v0.1.schema.json",
}
FIXTURE_DIR = ROOT / "tests/conformance/fixtures"
CASE_FILE = ROOT / "tests/conformance/cases.json"
INVALID_FIXTURES = {
    "malformed-envelope.json": "envelope",
    "missing-collection-timestamp.json": "manifest",
    "invalid-integrity-metadata.json": "envelope",
    "failed-assessment-pass.json": "assessment",
}
VALID_FIXTURES = {
    "envelope.json": "envelope",
    "collection-manifest.json": "manifest",
    "observation.json": "observation",
    "assessment-result.json": "assessment",
}
REQUIRED_CASE_IDS = {
    "identical-observations-across-runs",
    "changed-configuration-same-pass",
    "same-evidence-stricter-evaluator",
    "missing-target-partial-collection",
    "confirmed-deletion",
    "same-display-name-new-native-identity",
    "renamed-object-stable-native-identity",
    "same-value-incompatible-schema-meanings",
    "equivalent-representation-with-documented-transformation",
    "malformed-envelope",
    "missing-collection-timestamp",
    "duplicate-envelope-submission",
    "replayed-older-evidence",
    "reduced-scope-between-runs",
    "collector-failure",
    "invalid-integrity-metadata",
    "unknown-rule-version",
    "relationship-drift-between-stable-objects",
    "completed-collection-partial-control-coverage",
    "failed-assessment-cannot-pass",
}
EXPECTED_DIMENSIONS = {
    "environment": {
        "no-drift", "drift", "unknown", "not-assessed",
    },
    "collection": {
        "stable", "changed", "incomplete", "failed", "invalid", "not-assessed",
    },
    "representation": {
        "comparable", "transformation-required", "incompatible", "invalid",
        "not-assessed",
    },
    "identity": {
        "same", "replacement", "ambiguous", "deleted", "unknown", "not-assessed",
    },
    "evaluation": {
        "unchanged", "changed", "unknown", "not-assessed",
    },
    "trust": {
        "acceptable-assertion", "warning", "error", "not-assessed",
    },
}
OPTIONAL_EXPECTED_DIMENSIONS = {
    "coverage": {"complete", "partial", "changed", "unknown", "not-assessed"},
}
CREDENTIAL_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{24,}"),
]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


class ValidationFailure(Exception):
    """Raised for invalid repository fixture or schema metadata."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationFailure(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        if path.stat().st_size > 1_000_000:
            raise ValidationFailure("JSON input exceeds the 1 MB validation limit")
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationFailure) as exc:
        raise ValidationFailure(f"{path.relative_to(ROOT)}: {exc}") from exc


def safe_repo_path(relative_path: str, base: Path) -> Path:
    candidate = (base / unquote(relative_path)).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise ValidationFailure(f"path escapes repository: {relative_path}") from exc
    return candidate


def validate_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    schema_ids: set[str] = set()
    for kind, path in SCHEMAS.items():
        schema = load_json(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ValidationFailure(f"{path.relative_to(ROOT)}: unexpected JSON Schema dialect")
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id or schema_id in schema_ids:
            raise ValidationFailure(f"{path.relative_to(ROOT)}: missing or duplicate $id")
        schema_ids.add(schema_id)
        if schema.get("properties", {}).get("contractVersion", {}).get("const") != "0.1":
            raise ValidationFailure(f"{path.relative_to(ROOT)}: contractVersion is not 0.1")
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise ValidationFailure(f"{path.relative_to(ROOT)}: invalid schema: {exc}") from exc
        schemas[kind] = schema
    return schemas


def validate_schema_fixtures(schemas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    format_checker = FormatChecker()
    valid_dir = FIXTURE_DIR / "schema-valid"
    invalid_dir = FIXTURE_DIR / "schema-invalid"
    valid_files = sorted(valid_dir.glob("*.json"))
    if {path.name for path in valid_files} != set(VALID_FIXTURES):
        raise ValidationFailure("schema-valid fixtures must provide exactly one instance per schema")

    loaded: dict[str, Any] = {}
    for path in valid_files:
        kind = VALID_FIXTURES[path.name]
        instance = load_json(path)
        errors = list(Draft202012Validator(
            schemas[kind], format_checker=format_checker
        ).iter_errors(instance))
        if errors:
            raise ValidationFailure(
                f"{path.relative_to(ROOT)}: expected valid, got "
                + "; ".join(error.message for error in errors)
            )
        loaded[kind] = instance

    actual_invalid_names = {path.name for path in invalid_dir.glob("*.json")}
    if actual_invalid_names != set(INVALID_FIXTURES):
        raise ValidationFailure("schema-invalid fixture inventory does not match validator expectations")
    for filename, kind in INVALID_FIXTURES.items():
        path = invalid_dir / filename
        instance = load_json(path)
        errors = list(Draft202012Validator(
            schemas[kind], format_checker=format_checker
        ).iter_errors(instance))
        if not errors:
            raise ValidationFailure(
                f"{path.relative_to(ROOT)}: expected schema rejection, but instance is valid"
            )

    envelope = loaded["envelope"]
    manifest = loaded["manifest"]
    observation = loaded["observation"]
    assessment = loaded["assessment"]
    if envelope["manifestId"] != manifest["manifestId"]:
        raise ValidationFailure("valid schema fixtures: envelope manifestId does not resolve")
    if envelope["collectionRunId"] != manifest["collectionRunId"]:
        raise ValidationFailure("valid schema fixtures: envelope and manifest run IDs differ")
    if envelope["observationIds"] != [observation["observationId"]]:
        raise ValidationFailure("valid schema fixtures: envelope observationIds do not resolve")
    if envelope["assessmentIds"] != [assessment["assessmentId"]]:
        raise ValidationFailure("valid schema fixtures: envelope assessmentIds do not resolve")
    if assessment["observationReferences"] != [observation["observationId"]]:
        raise ValidationFailure("valid schema fixtures: assessment observation reference does not resolve")
    return loaded


def validate_cases() -> int:
    case_set = load_json(CASE_FILE)
    if case_set.get("caseSetVersion") != "0.1" or case_set.get("schemaSetVersion") != "0.1":
        raise ValidationFailure("cases.json must declare caseSetVersion and schemaSetVersion 0.1")
    spec_link = case_set.get("architectureSpecification", "")
    if not spec_link.endswith("/specifications/evidence-envelope-v0.1.md"):
        raise ValidationFailure("cases.json must link to the authoritative architecture specification")

    cases = case_set.get("cases")
    if not isinstance(cases, list):
        raise ValidationFailure("cases.json must contain a cases array")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or len(set(identifiers)) != len(identifiers):
        raise ValidationFailure("case IDs must be present and unique")
    if set(identifiers) != REQUIRED_CASE_IDS:
        missing = sorted(REQUIRED_CASE_IDS - set(identifiers))
        extra = sorted(set(identifiers) - REQUIRED_CASE_IDS)
        raise ValidationFailure(f"case inventory mismatch; missing={missing}, extra={extra}")

    referenced_invalid: set[str] = set()
    for case in cases:
        if not isinstance(case.get("scenario"), str) or not case["scenario"].strip():
            raise ValidationFailure(f"{case['id']}: missing scenario description")
        if not isinstance(case.get("rationale"), str) or not case["rationale"].strip():
            raise ValidationFailure(f"{case['id']}: missing rationale")
        inputs = case.get("inputs")
        if not isinstance(inputs, dict) or not inputs:
            raise ValidationFailure(f"{case['id']}: missing synthetic inputs")
        expected = case.get("expected")
        if not isinstance(expected, dict) or not isinstance(expected.get("result"), str):
            raise ValidationFailure(f"{case['id']}: missing machine-readable expected result")
        for dimension, permitted in EXPECTED_DIMENSIONS.items():
            if expected.get(dimension) not in permitted:
                raise ValidationFailure(
                    f"{case['id']}: missing or invalid expected {dimension} outcome"
                )
        for dimension, permitted in OPTIONAL_EXPECTED_DIMENSIONS.items():
            if dimension in expected and expected[dimension] not in permitted:
                raise ValidationFailure(
                    f"{case['id']}: invalid expected {dimension} outcome"
                )
        if (
            case["id"] == "completed-collection-partial-control-coverage"
            and expected.get("coverage") != "partial"
        ):
            raise ValidationFailure(
                f"{case['id']}: expected coverage must explicitly be partial"
            )
        fixture_name = inputs.get("schemaFixture")
        if fixture_name is not None:
            if not isinstance(fixture_name, str):
                raise ValidationFailure(f"{case['id']}: unsafe schemaFixture path")
            filename = Path(fixture_name).name
            expected_path = f"fixtures/schema-invalid/{filename}"
            if fixture_name != expected_path:
                raise ValidationFailure(f"{case['id']}: unsafe schemaFixture path")
            if filename not in INVALID_FIXTURES:
                raise ValidationFailure(f"{case['id']}: unknown schemaFixture {filename}")
            referenced_invalid.add(filename)
            safe_repo_path(fixture_name, CASE_FILE.parent)
    if referenced_invalid != set(INVALID_FIXTURES):
        raise ValidationFailure("every deliberately-invalid schema fixture must be referenced by a case")
    return len(cases)


def repository_text_files() -> list[Path]:
    paths = [ROOT / "README.md"]
    for directory in (
        ROOT / ".github/carl",
        ROOT / "schemas",
        ROOT / "tests/conformance",
        ROOT / "tools",
    ):
        paths.extend(directory.rglob("*.md"))
        paths.extend(directory.rglob("*.json"))
        paths.extend(directory.rglob("*.py"))
        paths.extend(directory.rglob("*.txt"))
    return sorted(set(path for path in paths if path.is_file()))


def validate_docs_and_text() -> None:
    try:
        safe_repo_path("../../../../../etc/passwd", CASE_FILE.parent)
    except ValidationFailure:
        pass
    else:
        raise ValidationFailure("path traversal guard accepted an outside-repository path")

    for path in repository_text_files():
        relative = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if text and not text.endswith("\n"):
            raise ValidationFailure(f"{relative}: missing final newline")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.endswith((" ", "\t")):
                raise ValidationFailure(f"{relative}:{line_number}: trailing whitespace")
        for pattern in CREDENTIAL_PATTERNS:
            if pattern.search(text):
                raise ValidationFailure(f"{relative}: possible credential pattern detected")
        if path.suffix != ".md":
            continue
        for match in MARKDOWN_LINK.finditer(text):
            target = match.group(1).strip().split()[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("#") or not parsed.path:
                continue
            linked_path = safe_repo_path(parsed.path, path.parent)
            if not linked_path.exists():
                raise ValidationFailure(
                    f"{relative}: broken local documentation link {target}"
                )


def main() -> int:
    try:
        version = importlib.metadata.version("jsonschema")
        if version != "4.26.0":
            raise ValidationFailure(
                f"jsonschema 4.26.0 is required by requirements-dev.txt; found {version}"
            )
        schemas = validate_schemas()
        validate_schema_fixtures(schemas)
        case_count = validate_cases()
        validate_docs_and_text()
    except (
        ValidationFailure,
        OSError,
        UnicodeError,
        importlib.metadata.PackageNotFoundError,
    ) as exc:
        print(f"conformance validation failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"schema and fixture-data checks passed: {len(schemas)} schemas, "
        f"{len(SCHEMAS)} valid fixtures, {len(INVALID_FIXTURES)} expected-invalid "
        f"fixtures, {case_count} semantic expectation cases."
    )
    print("No semantic comparison, digest verification, or source-truth test was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
