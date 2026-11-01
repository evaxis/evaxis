#!/usr/bin/env python3
"""Experimental capture validation and atomic Evidence Envelope assembly."""

from __future__ import annotations

import argparse
import copy
import ctypes
import csv
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from functools import lru_cache
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_conformance import (  # noqa: E402
    CREDENTIAL_PATTERNS, SCHEMAS, ValidationFailure, evidence_format_checker,
    target_key, target_set, validate_package,
)

CAPTURE_SCHEMA = ROOT / "capture" / "contracts" / "capture-v0.1.schema.json"
EXTENSION = "evaxis.capture/0.1"
MAX_BYTES = 1_000_000
SECRET_KEYS = {
    "accesstoken", "refreshtoken", "authorization", "clientsecret",
    "password", "privatekey", "credential", "credentials",
    "token", "secret", "apikey", "secretkey", "sharedaccesssignature", "connectionstring",
}


class CaptureFailure(Exception):
    """A safe diagnostic that never includes source values."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CaptureFailure("duplicate JSON object key")
        result[key] = value
    return result


def check_json_value(value: Any, depth: int = 0) -> None:
    if depth > 32:
        raise CaptureFailure("JSON nesting exceeds the capture limit")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or re.sub(r"[-_]", "", key).lower() in SECRET_KEYS:
                raise CaptureFailure("non-string or prohibited credential field")
            check_json_value(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            check_json_value(item, depth + 1)
    elif isinstance(value, str) and any(pattern.search(value) for pattern in CREDENTIAL_PATTERNS):
        raise CaptureFailure("prohibited credential value")
    elif value is not None and not isinstance(value, (str, bool, int, float)):
        raise CaptureFailure("input is not a JSON value")
    elif isinstance(value, float) and (value != value or abs(value) == float("inf")):
        raise CaptureFailure("non-finite JSON number")


def decode_json(data: bytes) -> Any:
    if len(data) > MAX_BYTES:
        raise CaptureFailure("JSON input exceeds the 1 MB capture limit")
    try:
        value = json.loads(
            data.decode("utf-8-sig"), object_pairs_hook=unique_object,
            parse_constant=reject_constant, parse_float=exact_float,
        )
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise CaptureFailure("invalid UTF-8 JSON input") from exc
    check_json_value(value)
    return value


def reject_constant(value: str) -> None:
    raise CaptureFailure("non-finite JSON number")


def exact_float(value: str) -> float:
    parsed = float(value)
    if abs(parsed) == float("inf"):
        raise CaptureFailure("non-finite JSON number")
    try:
        preserved = Decimal(str(parsed)) == Decimal(value)
    except InvalidOperation as exc:
        raise CaptureFailure("JSON numeric precision cannot be preserved by this implementation") from exc
    if not preserved:
        raise CaptureFailure("JSON numeric precision cannot be preserved by this implementation")
    return parsed


def safe_path(path: Path, *, must_exist: bool = True) -> Path:
    if ".." in path.parts or (os.name == "nt" and str(path).startswith("\\\\")):
        raise CaptureFailure("traversal, network, and device paths are unsupported")
    absolute = Path(os.path.abspath(path))
    for component in (*reversed(absolute.parents), absolute):
        try:
            info = component.lstat()
        except FileNotFoundError:
            if component != absolute or must_exist:
                raise CaptureFailure("input or output parent does not exist") from None
            continue
        except OSError as exc:
            raise CaptureFailure("cannot inspect input or output path") from exc
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
        ):
            raise CaptureFailure("symlink or reparse path is unsupported")
    return absolute


def read_json(path: Path) -> Any:
    safe = safe_path(path)
    try:
        with safe.open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
    except OSError as exc:
        raise CaptureFailure("cannot read JSON input") from exc
    return decode_json(data)


@lru_cache(maxsize=1)
def schema_set() -> tuple[dict[str, Any], Registry]:
    schemas = {kind: read_json(path) for kind, path in SCHEMAS.items()}
    schemas["capture"] = read_json(CAPTURE_SCHEMA)
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas.values()
    )
    return schemas, registry


def validate_shape(value: Any, kind: str) -> None:
    schemas, registry = schema_set()
    errors = Draft202012Validator(
        schemas[kind], registry=registry, format_checker=evidence_format_checker()
    ).iter_errors(value)
    if next(errors, None) is not None:
        # JSON Schema error messages may contain entire confidential payloads.
        raise CaptureFailure(f"{kind} schema validation rejected input")


def event_time(value: str) -> tuple[datetime, Decimal]:
    try:
        parsed = datetime.fromisoformat(value.replace("t", "T").replace("z", "Z").replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
        fraction = re.search(r"\.(\d+)", value)
        return (
            parsed.replace(microsecond=0),
            Decimal("0." + fraction.group(1)) if fraction else Decimal(0),
        )
    except (ValueError, TypeError) as exc:
        raise CaptureFailure("timestamp must include an explicit UTC offset") from exc


def scope_key(scope: dict[str, Any]) -> tuple[str, str]:
    values = scope["authority"], scope["scopeId"]
    if any(not value.strip() for value in values):
        raise CaptureFailure("source authority and scope must be nonblank")
    return values


def checked_targets(values: list[dict[str, Any]], scope: tuple[str, str]) -> set[tuple[str, str, str]]:
    try:
        result = target_set(values, "capture target set")
    except ValidationFailure as exc:
        raise CaptureFailure("duplicate target identity") from exc
    if any(key[:2] != scope or not key[2].strip() for key in result):
        raise CaptureFailure("target lacks native identity or belongs to another scope")
    return result


def validate_capture(capture: Any, *, final: bool = True) -> None:
    check_json_value(capture)
    validate_shape(capture, "capture")
    if final and capture["state"] != "completed":
        raise CaptureFailure("only completed capture runs can be assembled")
    run_id = capture["collectionRunId"]
    if any(not capture["collector"][key].strip() for key in ("authority", "id", "version")):
        raise CaptureFailure("collector identity and version must be nonblank")
    if "collectorConfiguration" in capture and not capture["collectorConfiguration"]["version"].strip():
        raise CaptureFailure("collector configuration version must be nonblank")
    scope = scope_key(capture["requestedScope"])
    if scope_key(capture["source"]) != scope:
        raise CaptureFailure("source authority/scope does not match requested scope")
    expected = checked_targets(capture["inventory"]["expectedTargets"], scope)
    started = event_time(capture["startedAt"])
    completed = event_time(capture["completedAt"]) if capture["state"] == "completed" else None
    if completed is not None and completed < started:
        raise CaptureFailure("collection completion precedes start")
    attempts: dict[str, Any] = {}
    intended_sets: dict[str, set[tuple[str, str, str]]] = {}
    for attempt in capture["sourceAttempts"]:
        attempt_id = attempt["attemptId"]
        if attempt_id in attempts:
            raise CaptureFailure("duplicate source attempt identifier")
        if attempt["collectionRunId"] != run_id or scope_key(attempt["intendedScope"]) != scope:
            raise CaptureFailure("source attempt belongs to another run or scope")
        intended = checked_targets(attempt["intendedTargets"], scope)
        if not intended <= expected:
            raise CaptureFailure("attempt target lies outside declared candidates")
        attempt_start = event_time(attempt["startedAt"])
        if attempt_start < started:
            raise CaptureFailure("attempt start precedes collection start")
        if attempt["status"] != "in-progress":
            if "completedAt" not in attempt:
                raise CaptureFailure("finished attempt lacks completion event")
            attempt_end = event_time(attempt["completedAt"])
            if attempt_end < attempt_start or (completed is not None and attempt_end > completed):
                raise CaptureFailure("attempt interval lies outside collection interval")
            if attempt["status"] != "succeeded" and not attempt.get("limitation"):
                raise CaptureFailure("non-success attempt requires a limitation")
        elif completed is not None:
            raise CaptureFailure("completed collection has an unresolved attempt")
        attempts[attempt_id] = attempt
        intended_sets[attempt_id] = intended

    observed: set[tuple[str, str, str]] = set()
    observation_ids: set[str] = set()
    attempt_observed: dict[str, set[tuple[str, str, str]]] = {key: set() for key in attempts}
    for item in capture["observations"]:
        record = item["record"]
        observation_id = record["observationId"]
        if observation_id in observation_ids:
            raise CaptureFailure("duplicate observation identifier")
        observation_ids.add(observation_id)
        if any(not record["observationSchema"][key].strip() for key in ("id", "version")):
            raise CaptureFailure("observation schema identity and version must be nonblank")
        if EXTENSION in record.get("extensions", {}):
            raise CaptureFailure("capture record uses the reserved assembly lineage namespace")
        if record["collectionRunId"] != run_id or record["collector"] != capture["collector"]:
            raise CaptureFailure("observation belongs to another run or collector")
        if record["source"] != capture["source"]:
            raise CaptureFailure("observation source does not match declared source")
        key = target_key(record["target"])
        if key not in expected:
            raise CaptureFailure("observation target was not declared")
        attempt_id = item["attemptId"]
        if attempt_id not in attempts or key not in intended_sets[attempt_id]:
            raise CaptureFailure("observation source attempt does not resolve for target")
        if attempts[attempt_id]["status"] in {"denied", "unavailable", "unsupported", "not-attempted"}:
            raise CaptureFailure("non-collecting source attempt cannot supply an observation")
        captured = event_time(item["capturedAt"])
        attempt = attempts[attempt_id]
        if captured < event_time(attempt["startedAt"]) or (
            "completedAt" in attempt and captured > event_time(attempt["completedAt"])
        ):
            raise CaptureFailure("observation capture event lies outside attempt interval")
        event_time(record["observedAt"])
        if item["observedAtProvenance"]["origin"] in {"evaluator-event", "framework-event"}:
            raise CaptureFailure("assessment time cannot be source observation time")
        for transformation in item["transformations"]:
            if transformation["outputReference"] != observation_id:
                raise CaptureFailure("transformation output does not identify its observation")
        observed.add(key)
        attempt_observed[attempt_id].add(key)

    not_observed = checked_targets([item["target"] for item in capture["notObserved"]], scope)
    if not_observed & observed or not not_observed <= expected:
        raise CaptureFailure("observed and not-observed target sets are inconsistent")
    for item in capture["notObserved"]:
        attempt_id = item["attemptId"]
        key = target_key(item["target"])
        if attempt_id not in attempts or key not in intended_sets[attempt_id]:
            raise CaptureFailure("not-observed source attempt does not resolve for target")
        attempt = attempts[attempt_id]
        if attempt["status"] in {"succeeded", "in-progress"} or (
            item["reason"] != "unknown" and item["reason"] != attempt["status"]
        ):
            raise CaptureFailure("not-observed reason contradicts source attempt")
        recorded = event_time(item["recordedAt"])
        if recorded < event_time(attempt["completedAt"]) or (completed is not None and recorded > completed):
            raise CaptureFailure("non-observation event lies outside collection interval")
    for attempt_id, attempt in attempts.items():
        if attempt["status"] == "succeeded" and attempt_observed[attempt_id] != intended_sets[attempt_id]:
            raise CaptureFailure("successful attempt did not observe every intended target")

    if completed is not None:
        coverage = capture["coverageStatus"]
        if capture["inventory"]["status"] == "unknown" and coverage != "unknown":
            raise CaptureFailure("unknown inventory cannot claim known coverage")
        if coverage == "complete" and (observed != expected or not_observed):
            raise CaptureFailure("complete coverage did not observe all declared targets")
        if coverage == "partial" and observed | not_observed != expected:
            raise CaptureFailure("partial coverage must account for every declared target")
        statuses = {attempt["status"] for attempt in attempts.values()}
        status = capture["collectionStatus"]
        if status == "succeeded" and (coverage != "complete" or statuses != {"succeeded"}):
            raise CaptureFailure("successful collection contradicts attempts or coverage")
        if status not in {"succeeded", "partial"} and (observed or statuses != {status}):
            raise CaptureFailure("collection failure state contradicts source attempts or observations")

    assessment_ids: set[str] = set()
    observation_map = {item["record"]["observationId"]: item["record"] for item in capture["observations"]}
    invocation_ids: set[str] = set()
    for item in capture["assessments"]:
        record = item["record"]
        assessment_id = record["assessmentId"]
        if assessment_id in assessment_ids:
            raise CaptureFailure("duplicate assessment identifier")
        assessment_ids.add(assessment_id)
        if EXTENSION in record.get("extensions", {}):
            raise CaptureFailure("capture record uses the reserved assembly lineage namespace")
        if any(not record[field][key].strip() for field in ("rule", "evaluator") for key in ("authority", "id", "version")):
            raise CaptureFailure("rule and evaluator identity and version must be nonblank")
        if item["collectionRunId"] != run_id:
            raise CaptureFailure("assessment belongs to another run")
        if target_key(record["subject"]) not in expected:
            raise CaptureFailure("assessment subject lies outside declared candidates")
        recorded = event_time(item["recordedAt"])
        if recorded < started or (completed is not None and recorded > completed):
            raise CaptureFailure("assessment capture event lies outside collection interval")
        if event_time(record["assessedAt"]) > recorded:
            raise CaptureFailure("assessment timestamp is later than its capture event")
        references = record["observationReferences"]
        if not set(references) <= observation_ids:
            raise CaptureFailure("assessment observation reference does not resolve")
        if record["inputBasis"]["kind"] == "observations" and not any(
            target_key(observation_map[reference]["target"]) == target_key(record["subject"])
            for reference in references
        ):
            raise CaptureFailure("assessment has no subject-matching observation")
        if item["assessedAtProvenance"]["origin"] not in {"evaluator-event", "framework-event", "caller-supplied"}:
            raise CaptureFailure("assessment timestamp provenance is invalid")
        assessed = checked_targets(record["controlCoverage"]["assessedSubjects"], scope)
        unassessed = checked_targets(
            [subject["target"] for subject in record["controlCoverage"]["unassessedSubjects"]], scope
        )
        if assessed & unassessed or not (assessed | unassessed) <= expected:
            raise CaptureFailure("assessment control coverage subjects are inconsistent")
        if record["controlCoverage"]["status"] == "complete" and unassessed:
            raise CaptureFailure("complete control coverage has unassessed subjects")
        if record["outcome"] in {"pass", "fail"} and target_key(record["subject"]) not in assessed:
            raise CaptureFailure("assessment conclusion lacks its assessed subject")
        association = item.get("frameworkAssociation")
        if association:
            framework = capture.get("frameworkContext")
            if not framework or association["executionId"] != framework["executionId"] or (
                association["collectionRunId"] != run_id
            ):
                raise CaptureFailure("execution-associated sidecar belongs to another run")
            if association["invocationId"] in invocation_ids:
                raise CaptureFailure("duplicate framework invocation association")
            invocation_ids.add(association["invocationId"])


def assemble(capture: dict[str, Any]) -> dict[str, Any]:
    validate_capture(capture)
    run_id = capture["collectionRunId"]
    observations: list[dict[str, Any]] = []
    assessments: list[dict[str, Any]] = []
    observation_lineage: list[dict[str, Any]] = []
    assessment_lineage: list[dict[str, Any]] = []
    for item in capture["observations"]:
        record = copy.deepcopy(item["record"])
        metadata = copy.deepcopy({key: value for key, value in item.items() if key != "record"})
        metadata["collectionRunId"] = run_id
        record.setdefault("extensions", {})[EXTENSION] = metadata
        observations.append(record)
        observation_lineage.append(dict(metadata, observationId=record["observationId"]))
    for item in capture["assessments"]:
        record = copy.deepcopy(item["record"])
        metadata = copy.deepcopy({key: value for key, value in item.items() if key != "record"})
        record.setdefault("extensions", {})[EXTENSION] = metadata
        assessments.append(record)
        assessment_lineage.append(dict(metadata, assessmentId=record["assessmentId"]))
    observed_by_key = {
        target_key(record["target"]): {
            key: record["target"][key] for key in ("authority", "scopeId", "nativeId", "displayName")
            if key in record["target"]
        }
        for record in observations
    }
    manifest: dict[str, Any] = {
        "manifestId": "manifest:" + run_id,
        "contractVersion": "0.1", "collectionRunId": run_id,
        "collector": copy.deepcopy(capture["collector"]),
        "startedAt": capture["startedAt"], "completedAt": capture["completedAt"],
        "collectionStatus": capture["collectionStatus"],
        "requestedScope": copy.deepcopy(capture["requestedScope"]),
        "sourceAttempts": [
            {
                "authority": attempt["intendedScope"]["authority"],
                "status": attempt["status"], "startedAt": attempt["startedAt"],
                "completedAt": attempt["completedAt"],
                **({"limitation": attempt["limitation"]["description"]} if "limitation" in attempt else {}),
            }
            for attempt in capture["sourceAttempts"]
        ],
        "coverage": {
            "status": capture["coverageStatus"],
            "expectedTargets": copy.deepcopy(capture["inventory"]["expectedTargets"]),
            "observedTargets": list(observed_by_key.values()),
            "notObserved": [
                {"target": copy.deepcopy(item["target"]), "reason": item["reason"]}
                for item in capture["notObserved"]
            ],
        },
    }
    constraints = [
        copy.deepcopy(constraint) for attempt in capture["sourceAttempts"]
        for constraint in attempt.get("visibilityConstraints", [])
    ]
    if constraints:
        manifest["visibilityConstraints"] = constraints
    if "collectorConfiguration" in capture:
        manifest["collectorConfiguration"] = copy.deepcopy(capture["collectorConfiguration"])
    lineage = {
        "captureContractVersion": "0.1", "collectionRunId": run_id,
        "source": copy.deepcopy(capture["source"]),
        "inventory": copy.deepcopy(capture["inventory"]),
        "sourceAttempts": copy.deepcopy(capture["sourceAttempts"]),
        "notObserved": copy.deepcopy(capture["notObserved"]),
        "observations": observation_lineage, "assessments": assessment_lineage,
    }
    if "frameworkContext" in capture:
        lineage["frameworkContext"] = copy.deepcopy(capture["frameworkContext"])
    envelope = {
        "contractVersion": "0.1", "envelopeId": "envelope:" + run_id,
        "producer": {
            key: capture["collector"][key] for key in ("authority", "id", "version")
        } | {"role": "collector"},
        "collectionRunId": run_id,
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifestId": manifest["manifestId"],
        "observationIds": [record["observationId"] for record in observations],
        "assessmentIds": [record["assessmentId"] for record in assessments],
        "integrity": {"claimStatus": "no-claim"},
        "extensions": {EXTENSION: lineage},
    }
    package = {"envelope": envelope, "manifest": manifest, "observations": observations, "assessments": assessments}
    validate_evidence_package(package)
    return package


def validate_evidence_package(package: Any) -> dict[str, Any]:
    if not isinstance(package, dict) or set(package) != {"envelope", "manifest", "observations", "assessments"}:
        raise CaptureFailure("package requires exactly envelope, manifest, observations, and assessments")
    if not isinstance(package["observations"], list) or not isinstance(package["assessments"], list):
        raise CaptureFailure("package observations and assessments must be arrays")
    check_json_value(package)
    for kind, records in (
        ("envelope", [package["envelope"]]), ("manifest", [package["manifest"]]),
        ("observation", package["observations"]), ("assessment", package["assessments"]),
    ):
        for record in records:
            validate_shape(record, kind)
    try:
        validate_package(package)
    except ValidationFailure as exc:
        raise CaptureFailure(str(exc)) from exc
    lineage = package["envelope"].get("extensions", {}).get(EXTENSION)
    if lineage is not None:
        if not isinstance(lineage, dict) or lineage.get("captureContractVersion") != "0.1" or (
            lineage.get("collectionRunId") != package["envelope"]["collectionRunId"]
        ):
            raise CaptureFailure("package capture lineage belongs to another contract or run")
        inventory = lineage.get("inventory", {})
        if inventory.get("status") == "unknown" and package["manifest"]["coverage"]["status"] != "unknown":
            raise CaptureFailure("unknown captured inventory cannot become complete coverage")
        for record in (*package["observations"], *package["assessments"]):
            metadata = record.get("extensions", {}).get(EXTENSION, {})
            if metadata.get("collectionRunId") != package["envelope"]["collectionRunId"]:
                raise CaptureFailure("record capture lineage belongs to another run")
        manifest = package["manifest"]
        reconstructed = {
            "captureContractVersion": "0.1", "envelopeContractVersion": "0.1",
            "collectionRunId": manifest["collectionRunId"], "state": "completed",
            "collector": manifest["collector"], "source": lineage.get("source"),
            "requestedScope": manifest["requestedScope"], "startedAt": manifest["startedAt"],
            "completedAt": manifest.get("completedAt"), "collectionStatus": manifest["collectionStatus"],
            "coverageStatus": manifest["coverage"]["status"], "inventory": inventory,
            "sourceAttempts": lineage.get("sourceAttempts"), "notObserved": lineage.get("notObserved"),
            "observations": [], "assessments": [],
        }
        for kind, identifier in (("observations", "observationId"), ("assessments", "assessmentId")):
            expected_lineage = []
            for record in package[kind]:
                original = copy.deepcopy(record)
                metadata = original["extensions"].pop(EXTENSION)
                if not original["extensions"]:
                    del original["extensions"]
                expected_lineage.append(dict(metadata, **{identifier: original[identifier]}))
                if kind == "observations":
                    metadata.pop("collectionRunId")
                reconstructed[kind].append(dict(metadata, record=original))
            if lineage.get(kind) != expected_lineage:
                raise CaptureFailure("envelope and record capture lineage disagree")
        for optional in ("collectorConfiguration",):
            if optional in manifest:
                reconstructed[optional] = manifest[optional]
        if "frameworkContext" in lineage:
            reconstructed["frameworkContext"] = lineage["frameworkContext"]
        validate_capture(reconstructed)
        expected_attempts = [
            {
                "authority": attempt["intendedScope"]["authority"], "status": attempt["status"],
                "startedAt": attempt["startedAt"], "completedAt": attempt["completedAt"],
                **({"limitation": attempt["limitation"]["description"]} if "limitation" in attempt else {}),
            }
            for attempt in lineage["sourceAttempts"]
        ]
        if manifest["sourceAttempts"] != expected_attempts or (
            manifest["coverage"]["expectedTargets"] != inventory["expectedTargets"]
        ) or manifest["coverage"]["notObserved"] != [
            {"target": item["target"], "reason": item["reason"]} for item in lineage["notObserved"]
        ]:
            raise CaptureFailure("manifest projection disagrees with preserved capture lineage")
        if manifest.get("visibilityConstraints", []) != [
            constraint for attempt in lineage["sourceAttempts"]
            for constraint in attempt.get("visibilityConstraints", [])
        ]:
            raise CaptureFailure("manifest visibility constraints disagree with preserved capture lineage")
    return {
        "schemaValidation": "passed", "packageConsistency": "passed",
        "observations": len(package["observations"]), "assessments": len(package["assessments"]),
        "receiverVerification": "not-performed", "sourceTruth": "not-established",
    }


def restrict_directory(path: Path) -> None:
    if os.name != "nt":
        path.chmod(0o700)
        return
    try:
        result = subprocess.run(
            ["whoami", "/user", "/fo", "csv", "/nh"],
            capture_output=True, text=True, check=True,
        )
        sid = next(csv.reader(io.StringIO(result.stdout)))[1]
        if not re.fullmatch(r"S-\d+(?:-\d+)+", sid):
            raise CaptureFailure("cannot determine output owner")
        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", f"*{sid}:(OI)(CI)F"],
            capture_output=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError, IndexError, StopIteration) as exc:
        raise CaptureFailure("cannot restrict output directory permissions") from exc


def finalize_directory(staging: Path, destination: Path) -> None:
    if os.name == "nt":
        os.rename(staging, destination)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        rename = libc.renameat2
    except AttributeError as exc:
        raise CaptureFailure("atomic no-replace directory publication is unsupported on this platform") from exc
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(staging), -100, os.fsencode(destination), 1) != 0:
        raise CaptureFailure("atomic no-replace directory publication failed")


def write_bundle(capture: dict[str, Any], destination: Path) -> dict[str, Any]:
    package = assemble(capture)
    destination = safe_path(destination, must_exist=False)
    if destination.exists():
        raise CaptureFailure("output destination already exists; overwrites are prohibited")
    staging: Path | None = None
    try:
        staging = Path(tempfile.mkdtemp(prefix=".evaxis-", dir=destination.parent))
        restrict_directory(staging)
        for name, value in (("capture.json", capture), ("package.json", package)):
            data = (json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2) + "\n").encode("utf-8")
            if len(data) > MAX_BYTES:
                raise CaptureFailure("assembled output exceeds the 1 MB per-file limit")
            with (staging / name).open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if os.name != "nt":
                (staging / name).chmod(0o600)
        safe_path(destination.parent)
        finalize_directory(staging, destination)
        staging = None
    except OSError as exc:
        raise CaptureFailure("atomic output finalization failed") from exc
    finally:
        if staging is not None:
            shutil.rmtree(staging)
    return validate_evidence_package(package)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("validate-capture", "assemble", "validate-package"))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--stdin", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if bool(args.input) == bool(args.stdin) or (args.operation == "assemble") != bool(args.output):
        parser.error("choose one input source; only assembly requires --output")
    try:
        value = decode_json(sys.stdin.buffer.read(MAX_BYTES + 1)) if args.stdin else read_json(args.input)
        if args.operation == "validate-capture":
            validate_capture(value)
            result = {"captureValidation": "passed"}
        elif args.operation == "assemble":
            result = write_bundle(value, args.output)
        else:
            result = validate_evidence_package(value)
    except (CaptureFailure, OSError) as exc:
        print(f"evidence operation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
