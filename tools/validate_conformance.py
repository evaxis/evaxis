#!/usr/bin/env python3
"""Validate Evidence Envelope schema and fixture consistency, not semantics."""

from __future__ import annotations

import importlib.metadata
import copy
import json
import re
import sys
from datetime import datetime
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
    "claims-verified-without-verification-claim.json": "envelope",
    "failed-assessment-pass.json": "assessment",
    "passing-assessment-without-basis.json": "assessment",
    "representation-content-and-reference.json": "observation",
}
VALID_FIXTURES = {
    "envelope.json": ("envelope", "envelope"),
    "collection-manifest.json": ("manifest", "manifest"),
    "observation.json": ("observation", "observation"),
    "observation-null-content.json": ("observation-null-content", "observation"),
    "assessment-result.json": ("assessment", "assessment"),
    "assessment-declared-scope.json": ("assessment-declared-scope", "assessment"),
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
    "passing-assessment-without-basis",
    "representation-content-and-reference",
}
REQUIRED_PACKAGE_CASE_IDS = {
    "complete-coverage-missing-observation",
    "complete-coverage-missing-target-accounting",
    "success-with-failed-source-attempt",
    "observation-run-mismatch",
    "unresolved-envelope-observation-reference",
    "unresolved-assessment-observation-reference",
    "duplicate-coverage-target",
    "coverage-target-overlap",
    "observed-target-outside-requested-scope",
    "unresolved-envelope-manifest-reference",
    "unresolved-envelope-assessment-reference",
    "assessment-observation-subject-mismatch",
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
        "assertion-only", "receiver-verification-premise", "warning", "error",
        "not-assessed",
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


def evidence_format_checker() -> FormatChecker:
    checker = FormatChecker()

    @checker.checks("date-time")
    def date_time(value: Any) -> bool:
        if not isinstance(value, str):
            return True
        if not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?"
            r"(?:[Zz]|[+-]\d{2}:[0-5]\d)",
            value,
        ):
            return False
        try:
            datetime.fromisoformat(
                value.replace("t", "T").replace("z", "Z").replace("Z", "+00:00")
            )
        except ValueError:
            return False
        return True

    return checker


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
    format_checker = evidence_format_checker()
    valid_dir = FIXTURE_DIR / "schema-valid"
    invalid_dir = FIXTURE_DIR / "schema-invalid"
    valid_files = sorted(valid_dir.glob("*.json"))
    if {path.name for path in valid_files} != set(VALID_FIXTURES):
        raise ValidationFailure("schema-valid fixtures must provide exactly one instance per schema")

    loaded: dict[str, Any] = {}
    for path in valid_files:
        record_key, kind = VALID_FIXTURES[path.name]
        instance = load_json(path)
        errors = list(Draft202012Validator(
            schemas[kind], format_checker=format_checker
        ).iter_errors(instance))
        if errors:
            raise ValidationFailure(
                f"{path.relative_to(ROOT)}: expected valid, got "
                + "; ".join(error.message for error in errors)
            )
        loaded[record_key] = instance

    null_observation = loaded["observation-null-content"]
    if "content" not in null_observation["representation"] or (
        null_observation["representation"]["content"] is not None
    ) or "reference" in null_observation["representation"]:
        raise ValidationFailure("null-content fixture must express explicit null without a reference")
    scoped_assessment = loaded["assessment-declared-scope"]
    if (
        scoped_assessment["executionStatus"] != "completed"
        or scoped_assessment["outcome"] != "pass"
        or scoped_assessment["inputBasis"]["kind"] != "declared-scope"
        or scoped_assessment["controlCoverage"]["status"] == "unknown"
    ):
        raise ValidationFailure("declared-scope assessment fixture must declare a supported non-unknown basis")

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
        if filename == "claims-verified-without-verification-claim.json" and not any(
            error.validator == "required"
            and list(error.path) == ["integrity"]
            and "verificationClaim" in error.message
            for error in errors
        ):
            raise ValidationFailure(
                f"{path.relative_to(ROOT)}: rejection must require verificationClaim"
            )

    valid_integrity = loaded["envelope"].get("integrity", {})
    if (
        valid_integrity.get("claimStatus") != "claims-verified"
        or not isinstance(valid_integrity.get("verificationClaim"), dict)
    ):
        raise ValidationFailure(
            "schema-valid envelope must demonstrate claims-verified with verificationClaim"
        )
    integrity_schema = schemas["envelope"]["$defs"]["integrity"]
    integrity_validator = Draft202012Validator(
        integrity_schema, format_checker=format_checker
    )
    for claim_status in integrity_schema["properties"]["claimStatus"]["enum"]:
        integrity = {"claimStatus": claim_status}
        errors = list(integrity_validator.iter_errors(integrity))
        if claim_status == "claims-verified" and not any(
            error.validator == "required"
            and "verificationClaim" in error.message
            for error in errors
        ):
            raise ValidationFailure(
                "claims-verified integrity without verificationClaim must be rejected"
            )
        if claim_status != "claims-verified" and errors:
            raise ValidationFailure(
                f"{claim_status} integrity must not require verificationClaim"
            )

    return loaded


def target_key(target: dict[str, Any]) -> tuple[str, str, str]:
    return target["authority"], target["scopeId"], target["nativeId"]


def target_set(targets: list[dict[str, Any]], label: str) -> set[tuple[str, str, str]]:
    keys = [target_key(target) for target in targets]
    if len(keys) != len(set(keys)):
        raise ValidationFailure(f"{label}: duplicate authority/scope/native target identity")
    return set(keys)


def validate_package(records: dict[str, Any]) -> None:
    envelope = records["envelope"]
    manifest = records["manifest"]
    observations = records["observations"] if "observations" in records else [records["observation"]]
    assessments = records["assessments"] if "assessments" in records else [records["assessment"]]

    if any(record["contractVersion"] != "0.1" for record in (
        envelope, manifest, *observations, *assessments
    )):
        raise ValidationFailure("package records must use contractVersion 0.1")

    if envelope["manifestId"] != manifest["manifestId"]:
        raise ValidationFailure("envelope manifestId does not resolve")
    if envelope["collectionRunId"] != manifest["collectionRunId"]:
        raise ValidationFailure("envelope and manifest run IDs differ")

    observation_ids = {observation["observationId"] for observation in observations}
    assessment_ids = {assessment["assessmentId"] for assessment in assessments}
    if len(observation_ids) != len(observations) or len(assessment_ids) != len(assessments):
        raise ValidationFailure("record identifiers must be unique within the package")
    if set(envelope["observationIds"]) != observation_ids:
        raise ValidationFailure("envelope observationIds do not resolve exactly to package observations")
    if set(envelope["assessmentIds"]) != assessment_ids:
        raise ValidationFailure("envelope assessmentIds do not resolve exactly to package assessments")

    coverage = manifest["coverage"]
    expected = target_set(coverage["expectedTargets"], "expectedTargets")
    observed = target_set(coverage["observedTargets"], "observedTargets")
    not_observed_targets = [item["target"] for item in coverage["notObserved"]]
    not_observed = target_set(not_observed_targets, "notObserved")
    if observed & not_observed:
        raise ValidationFailure("a target cannot be both observed and notObserved")
    if not (observed | not_observed) <= expected:
        raise ValidationFailure("observed/notObserved targets must be members of expectedTargets")
    if coverage["status"] == "complete" and (
        observed != expected or not_observed
    ):
        raise ValidationFailure("complete coverage must observe every expected target")
    if coverage["status"] == "partial" and observed | not_observed != expected:
        raise ValidationFailure("partial coverage must account for every expected target")
    if manifest["collectionStatus"] == "succeeded":
        if coverage["status"] != "complete":
            raise ValidationFailure("succeeded collection requires complete declared-scope coverage")
        if any(attempt["status"] != "succeeded" for attempt in manifest["sourceAttempts"]):
            raise ValidationFailure("succeeded collection cannot contain a non-succeeded source attempt")

    observation_targets: set[tuple[str, str, str]] = set()
    for observation in observations:
        if observation["collectionRunId"] != manifest["collectionRunId"]:
            raise ValidationFailure("observation collectionRunId does not match package manifest")
        target = observation["target"]
        if (
            observation["source"]["authority"] != target["authority"]
            or observation["source"]["scopeId"] != target["scopeId"]
        ):
            raise ValidationFailure("observation source authority/scope does not match its target")
        if any(
            observation["collector"][key] != manifest["collector"][key]
            for key in ("authority", "id", "version")
        ):
            raise ValidationFailure("observation collector does not match package manifest")
        if observation["source"]["authority"] not in {
            attempt["authority"] for attempt in manifest["sourceAttempts"]
        }:
            raise ValidationFailure("observation source has no declared source attempt")
        observation_targets.add(target_key(target))
    if observation_targets != observed:
        raise ValidationFailure("manifest observedTargets do not match package observation targets")

    observations_by_id = {observation["observationId"]: observation for observation in observations}
    for assessment in assessments:
        references = assessment["observationReferences"]
        if any(reference not in observations_by_id for reference in references):
            raise ValidationFailure("assessment observation reference does not resolve in package")
        basis = assessment["inputBasis"]
        if basis["kind"] == "observations":
            if not references:
                raise ValidationFailure("observation-based assessment must reference an observation")
            subject = target_key(assessment["subject"])
            if not any(
                target_key(observations_by_id[reference]["target"]) == subject
                for reference in references
            ):
                raise ValidationFailure("observation-based assessment has no subject-matching observation")
        if basis["kind"] == "external-references" and not basis.get("externalReferences"):
            raise ValidationFailure("external-reference assessment basis is empty")
        control = assessment["controlCoverage"]
        assessed = target_set(control["assessedSubjects"], "assessedSubjects")
        unassessed = target_set(
            [item["target"] for item in control["unassessedSubjects"]],
            "unassessedSubjects",
        )
        if assessed & unassessed:
            raise ValidationFailure("control coverage subjects overlap")
        if control["status"] == "complete" and unassessed:
            raise ValidationFailure("complete control coverage has unassessed subjects")
        if assessment["executionStatus"] != "completed" and assessment["outcome"] != "unknown":
            raise ValidationFailure("non-completed assessment must have unknown outcome")
        if assessment["outcome"] in {"pass", "fail"} and (
            basis["kind"] == "no-input"
            or control["status"] == "unknown"
            or target_key(assessment["subject"]) not in assessed
        ):
            raise ValidationFailure("conclusion requires legitimate input and assessed subject")


def validate_package_negative_cases(
    cases: list[dict[str, Any]], records: dict[str, Any]
) -> int:
    if not isinstance(cases, list):
        raise ValidationFailure("packageConsistencyCases must be an array")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if (
        len(identifiers) != len(cases)
        or len(set(identifiers)) != len(identifiers)
        or set(identifiers) != REQUIRED_PACKAGE_CASE_IDS
    ):
        raise ValidationFailure("package consistency case inventory must have unique required IDs")

    mutations = {
        "clear-observed-targets": lambda package: package["manifest"]["coverage"].update(
            observedTargets=[]
        ),
        "clear-observed-and-not-observed": lambda package: package["manifest"]["coverage"].update(
            observedTargets=[], notObserved=[]
        ),
        "fail-source-attempt": lambda package: package["manifest"]["sourceAttempts"][0].update(
            status="failed"
        ),
        "change-observation-run": lambda package: package["observation"].update(
            collectionRunId="urn:example:other-run"
        ),
        "reference-missing-observation": lambda package: package["envelope"].update(
            observationIds=["urn:example:missing-observation"]
        ),
        "reference-missing-assessment-observation": lambda package: package["assessment"].update(
            observationReferences=["urn:example:missing-observation"]
        ),
        "reference-missing-manifest": lambda package: package["envelope"].update(
            manifestId="urn:example:missing-manifest"
        ),
        "reference-missing-assessment": lambda package: package["envelope"].update(
            assessmentIds=["urn:example:missing-assessment"]
        ),
        "assessment-subject-mismatch": lambda package: package["assessment"]["subject"].update(
            nativeId="synthetic-other-object"
        ),
        "duplicate-expected-target": lambda package: package["manifest"]["coverage"][
            "expectedTargets"
        ].append(dict(package["manifest"]["coverage"]["expectedTargets"][0], displayName="duplicate")),
        "overlap-observed-and-not-observed": lambda package: package["manifest"]["coverage"][
            "notObserved"
        ].append({
            "target": dict(package["manifest"]["coverage"]["observedTargets"][0]),
            "reason": "unknown",
        }),
        "add-observed-target-outside-requested-scope": lambda package: package["manifest"][
            "coverage"
        ]["observedTargets"].append({
            "authority": "urn:example:source-authority",
            "scopeId": "synthetic-workspace",
            "nativeId": "unexpected-target",
        }),
    }
    for case in cases:
        if (
            case.get("expected") != "reject"
            or not isinstance(case.get("rationale"), str)
            or not case["rationale"].strip()
            or case.get("mutation") not in mutations
        ):
            raise ValidationFailure(f"{case.get('id')}: malformed package consistency case")
        mutated = copy.deepcopy(records)
        mutations[case["mutation"]](mutated)
        try:
            validate_package(mutated)
        except ValidationFailure:
            continue
        raise ValidationFailure(f"{case['id']}: invalid package mutation was accepted")
    return len(cases)


def validate_cases(records: dict[str, Any]) -> tuple[int, int]:
    case_set = load_json(CASE_FILE)
    if case_set.get("caseSetVersion") != "0.1" or case_set.get("schemaSetVersion") != "0.1":
        raise ValidationFailure("cases.json must declare caseSetVersion and schemaSetVersion 0.1")
    layers = case_set.get("conformanceLayers")
    required_layers = {
        "schemaFixtures",
        "packageConsistency",
        "semanticExpectations",
        "behavioralImplementationTests",
    }
    if not isinstance(layers, dict) or set(layers) != required_layers or any(
        not isinstance(value, str) or not value.strip() for value in layers.values()
    ):
        raise ValidationFailure("cases.json must declare all four conformance layers")
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
        if case.get("vectorKind") != "semantic-expectation-only":
            raise ValidationFailure(f"{case['id']}: semantic expectations must not be presented as executed vectors")
        preconditions = case.get("preconditions")
        if not isinstance(preconditions, dict) or set(preconditions) != {
            "scope", "collection", "identity", "representation", "freshness", "trust"
        } or any(not isinstance(value, str) or not value.strip() for value in preconditions.values()):
            raise ValidationFailure(f"{case['id']}: complete declared preconditions are required")
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
        if expected["environment"] in {"drift", "no-drift"}:
            comparison_context = inputs.get("comparisonContext")
            trust_premise = (
                comparison_context.get("receiverVerificationPremise")
                if isinstance(comparison_context, dict)
                else None
            )
            if (
                expected["trust"] != "receiver-verification-premise"
                or not isinstance(trust_premise, dict)
                or trust_premise.get("status") != "stipulated-success"
                or not trust_premise.get("policy")
                or not trust_premise.get("appliesTo")
                or not trust_premise.get("note")
            ):
                raise ValidationFailure(
                    f"{case['id']}: environmental conclusion requires an explicit receiver-trust premise"
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
    validate_package(records)
    package_case_count = validate_package_negative_cases(
        case_set.get("packageConsistencyCases", []), records
    )
    return len(cases), package_case_count


def repository_text_files() -> list[Path]:
    paths = [ROOT / "README.md"]
    for directory in (
        ROOT / ".github/carl",
        ROOT / "schemas",
        ROOT / "tests/conformance",
        ROOT / "tools",
        ROOT / "capture",
        ROOT / "integrations",
        ROOT / "examples/evidence-preservation",
        ROOT / "tests/capture",
        ROOT / "docs",
    ):
        paths.extend(directory.rglob("*.md"))
        paths.extend(directory.rglob("*.json"))
        paths.extend(directory.rglob("*.py"))
        paths.extend(directory.rglob("*.txt"))
        paths.extend(directory.rglob("*.ps1"))
        paths.extend(directory.rglob("*.psm1"))
        paths.extend(directory.rglob("*.psd1"))
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
        case_count, package_case_count = validate_cases(validate_schema_fixtures(schemas))
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
        f"{len(VALID_FIXTURES)} valid fixtures, {len(INVALID_FIXTURES)} expected-invalid "
        f"fixtures, {package_case_count} package-consistency rejection cases, "
        f"{case_count} semantic expectation cases."
    )
    print("No semantic comparison, digest verification, or source-truth test was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
