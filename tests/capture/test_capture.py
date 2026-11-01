"""Executable schema, capture, package, filesystem, and offline integration tests."""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from capture import package as evidence  # noqa: E402

GOLDEN = ROOT / "examples" / "evidence-preservation" / "golden"
CASES = evidence.read_json(Path(__file__).with_name("cases.json"))


def pointer(document: object, path: str) -> object:
    current = document
    for part in path.lstrip("/").split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        current = current[int(key)] if isinstance(current, list) else current[key]
    return current


def mutate(document: dict, operations: list[dict]) -> dict:
    result = copy.deepcopy(document)
    for operation in operations:
        parent_path, _, raw_key = operation["path"].rpartition("/")
        parent = pointer(result, parent_path) if parent_path else result
        key = raw_key.replace("~1", "/").replace("~0", "~")
        value = copy.deepcopy(pointer(result, operation["from"])) if operation["op"] == "copy" else operation.get("value")
        if isinstance(parent, list):
            if operation["op"] == "remove":
                del parent[int(key)]
            elif key == "-":
                parent.append(value)
            else:
                parent[int(key)] = value
        elif operation["op"] == "remove":
            del parent[key]
        else:
            parent[key] = value
    return result


class MutationFixtures(unittest.TestCase):
    def test_fixture_inventory(self) -> None:
        self.assertEqual(CASES["fixtureVersion"], "0.1")
        for layer in ("captureCases", "packageCases"):
            self.assertEqual(len(CASES[layer]), len({case["id"] for case in CASES[layer]}))
            self.assertGreaterEqual(len(CASES[layer]), 20)


def fixture_test(case: dict, *, capture: bool):
    def run(self: unittest.TestCase) -> None:
        data = evidence.read_json(GOLDEN / ("capture.json" if capture else "package.json"))
        changed = mutate(data, case["mutations"])
        with self.assertRaisesRegex(evidence.CaptureFailure, re.escape(case["error"])):
            (evidence.validate_capture if capture else evidence.validate_evidence_package)(changed)
    return run


for layer, capture in (("captureCases", True), ("packageCases", False)):
    for case in CASES[layer]:
        setattr(MutationFixtures, f"test_{layer}_{case['id'].replace('-', '_')}", fixture_test(case, capture=capture))


class CaptureAndAssembly(unittest.TestCase):
    def setUp(self) -> None:
        self.capture = evidence.read_json(GOLDEN / "capture.json")

    def test_real_golden_has_complete_provenance(self) -> None:
        evidence.validate_capture(self.capture)
        package = evidence.read_json(GOLDEN / "package.json")
        report = evidence.validate_evidence_package(package)
        self.assertEqual((report["observations"], report["assessments"]), (2, 3))
        source = evidence.read_json(ROOT / "examples" / "evidence-preservation" / "synthetic-source.json")
        for actual, original in zip(package["observations"], source["objects"]):
            self.assertEqual(actual["representation"], original["representation"])
            self.assertEqual(actual["observedAt"], original["observedAt"])
            self.assertEqual(actual["target"], original["target"])
            self.assertNotIn("digest", actual["representation"])
            self.assertEqual(actual["extensions"][evidence.EXTENSION]["transformations"], [])
        self.assertEqual([record["outcome"] for record in package["assessments"]], ["pass", "fail", "unknown"])
        self.assertEqual(package["assessments"][2]["observationReferences"], [])
        self.assertEqual(package["manifest"]["coverage"]["status"], "partial")
        self.assertEqual(package["envelope"]["integrity"], {"claimStatus": "no-claim"})

    def test_assembly_does_not_mutate_input(self) -> None:
        before = copy.deepcopy(self.capture)
        evidence.assemble(self.capture)
        self.assertEqual(self.capture, before)

    def test_partial_capture_positive(self) -> None:
        self.assertEqual(evidence.validate_evidence_package(evidence.assemble(self.capture))["packageConsistency"], "passed")

    def test_unknown_inventory_positive(self) -> None:
        self.capture["inventory"]["status"] = "unknown"
        self.capture["coverageStatus"] = "unknown"
        package = evidence.assemble(self.capture)
        self.assertEqual(package["manifest"]["coverage"]["status"], "unknown")
        self.assertEqual(len(package["manifest"]["coverage"]["expectedTargets"]), 3)

    def test_complete_declared_candidate_set_positive(self) -> None:
        self.capture["inventory"]["expectedTargets"].pop()
        self.capture["sourceAttempts"].pop()
        self.capture["assessments"].pop()
        self.capture["notObserved"] = []
        self.capture["collectionStatus"] = "succeeded"
        self.capture["coverageStatus"] = "complete"
        self.assertEqual(evidence.validate_evidence_package(evidence.assemble(self.capture))["observations"], 2)

    def test_multiple_observations_for_one_target(self) -> None:
        duplicate = copy.deepcopy(self.capture["observations"][0])
        duplicate["record"]["observationId"] = "second-observation-for-same-target"
        self.capture["observations"].append(duplicate)
        self.assertEqual(evidence.validate_evidence_package(evidence.assemble(self.capture))["observations"], 3)

    def test_empty_explicit_scope_does_not_invent_observations(self) -> None:
        self.capture["inventory"]["expectedTargets"] = []
        self.capture["sourceAttempts"] = [self.capture["sourceAttempts"][0]]
        self.capture["sourceAttempts"][0]["intendedTargets"] = []
        self.capture["observations"] = []
        self.capture["assessments"] = []
        self.capture["notObserved"] = []
        self.capture["collectionStatus"] = "succeeded"
        self.capture["coverageStatus"] = "complete"
        report = evidence.validate_evidence_package(evidence.assemble(self.capture))
        self.assertEqual((report["observations"], report["assessments"]), (0, 0))

    def test_initial_collecting_document_is_valid_but_not_exportable(self) -> None:
        self.capture["state"] = "collecting"
        for name in ("completedAt", "collectionStatus", "coverageStatus"):
            del self.capture[name]
        for name in ("sourceAttempts", "observations", "notObserved", "assessments"):
            self.capture[name] = []
        evidence.validate_capture(self.capture, final=False)
        with self.assertRaisesRegex(evidence.CaptureFailure, "only completed capture"):
            evidence.assemble(self.capture)

    def test_legitimate_declared_scope_assessment_without_observation(self) -> None:
        item = self.capture["assessments"][0]
        item["record"]["inputBasis"] = {"kind": "declared-scope", "rationale": "Synthetic producer explicitly declares a scope-based rule; validation does not verify its reasoning."}
        item["record"]["observationReferences"] = []
        evidence.assemble(self.capture)

    def test_legitimate_external_input_without_observation(self) -> None:
        item = self.capture["assessments"][0]
        item["record"]["inputBasis"] = {
            "kind": "external-references", "rationale": "Explicit external synthetic input, not an invented observation.",
            "externalReferences": ["urn:evaxis:synthetic-external-input"],
        }
        item["record"]["observationReferences"] = []
        evidence.assemble(self.capture)

    def test_framework_result_claim_remains_opaque(self) -> None:
        self.capture["assessments"][0]["frameworkAssociation"]["resultClaim"] = "framework-specific-opaque-claim"
        report = evidence.validate_evidence_package(evidence.assemble(self.capture))
        self.assertEqual(report["receiverVerification"], "not-performed")

    def test_producer_verification_is_not_receiver_verification(self) -> None:
        package = evidence.assemble(self.capture)
        package["envelope"]["integrity"] = {
            "claimStatus": "claims-verified",
            "verificationClaim": {
                "claimedVerifier": "synthetic-producer", "claimedAt": package["envelope"]["createdAt"],
                "claimedMethod": "synthetic-assertion-not-verification",
            },
        }
        package["envelope"]["extensions"]["producer-receiver-verification-claim"] = {"status": "verified"}
        before = copy.deepcopy(package)
        report = evidence.validate_evidence_package(package)
        self.assertEqual(report["receiverVerification"], "not-performed")
        self.assertEqual(report["sourceTruth"], "not-established")
        self.assertEqual(package, before)

    def test_schema_failure_does_not_expose_sensitive_value(self) -> None:
        sentinel = "synthetic-sensitive-content-never-log"
        self.capture["observations"][0]["record"]["representation"]["content"]["sensitiveValue"] = sentinel
        self.capture["observations"][0]["record"]["observedAt"] = "invalid"
        with self.assertRaises(evidence.CaptureFailure) as caught:
            evidence.validate_capture(self.capture)
        self.assertNotIn(sentinel, str(caught.exception))

    def test_duplicate_json_keys_do_not_expose_names(self) -> None:
        with self.assertRaisesRegex(evidence.CaptureFailure, "duplicate JSON object key"):
            evidence.decode_json(b'{"syntheticSensitiveKey":1,"syntheticSensitiveKey":2}')

    def test_json_size_limit(self) -> None:
        with self.assertRaisesRegex(evidence.CaptureFailure, "1 MB"):
            evidence.decode_json(b" " * (evidence.MAX_BYTES + 1))

    def test_json_depth_limit(self) -> None:
        data = b"[" * 34 + b"0" + b"]" * 34
        with self.assertRaisesRegex(evidence.CaptureFailure, "nesting"):
            evidence.decode_json(data)

    def test_non_finite_json_number(self) -> None:
        with self.assertRaisesRegex(evidence.CaptureFailure, "non-finite"):
            evidence.decode_json(b'{"number":NaN}')

    def test_invalid_utf8_json(self) -> None:
        with self.assertRaisesRegex(evidence.CaptureFailure, "invalid UTF-8"):
            evidence.decode_json(b'{"invalid":"\xff"}')

    def test_recognizable_credential_value_is_rejected_without_logging(self) -> None:
        value = "ghp_" + "x" * 36
        with self.assertRaisesRegex(evidence.CaptureFailure, "prohibited credential value") as caught:
            evidence.decode_json(json.dumps({"value": value}).encode())
        self.assertNotIn(value, str(caught.exception))
        with self.assertRaisesRegex(evidence.CaptureFailure, "prohibited credential field"):
            evidence.decode_json(b'{"api_key":"synthetic-sensitive-sentinel"}')

    def test_date_time_checks_do_not_depend_on_optional_format_packages(self) -> None:
        checker = evidence.evidence_format_checker()
        self.assertTrue(checker.conforms("2026-01-02T03:04:00+00:00", "date-time"))
        for invalid in ("not-a-time", "2026-01-02T03:04:00", "2026-01-02T03:04:00+00:99", "2026-02-30T03:04:00Z"):
            self.assertFalse(checker.conforms(invalid, "date-time"))

    def test_nonportable_numeric_precision_fails_instead_of_changing_evidence(self) -> None:
        with self.assertRaisesRegex(evidence.CaptureFailure, "numeric precision cannot be preserved"):
            evidence.decode_json(b'{"value":0.123456789012345678901}')
        self.assertEqual(evidence.decode_json(b'{"value":0.1}')["value"], 0.1)

    def test_submicrosecond_capture_event_after_attempt_completion_is_rejected(self) -> None:
        start = self.capture["sourceAttempts"][0]["startedAt"]
        self.capture["sourceAttempts"][0]["completedAt"] = start
        self.capture["observations"][0]["capturedAt"] = re.sub(
            r"\.(\d+)", lambda match: "." + str(int(match.group(1)) + 1).zfill(len(match.group(1))), start
        )
        with self.assertRaisesRegex(evidence.CaptureFailure, "capture event lies outside attempt interval"):
            evidence.validate_capture(self.capture)

    def test_invalid_timestamp_in_package_without_capture_extension(self) -> None:
        package = evidence.assemble(self.capture)
        del package["envelope"]["extensions"]
        for record in (*package["observations"], *package["assessments"]):
            del record["extensions"]
        package["observations"][0]["observedAt"] = "not-a-time"
        with self.assertRaisesRegex(evidence.CaptureFailure, "observation schema"):
            evidence.validate_evidence_package(package)

    def test_no_network_during_assembly(self) -> None:
        with patch("socket.socket", side_effect=AssertionError("network use is forbidden")):
            evidence.assemble(self.capture)


class FilesystemAndCommands(unittest.TestCase):
    def setUp(self) -> None:
        self.capture = evidence.read_json(GOLDEN / "capture.json")

    def test_atomic_private_output_and_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "bundle"
            evidence.write_bundle(self.capture, destination)
            self.assertEqual(set(path.name for path in destination.iterdir()), {"capture.json", "package.json"})
            evidence.validate_capture(evidence.read_json(destination / "capture.json"))
            evidence.validate_evidence_package(evidence.read_json(destination / "package.json"))
            if os.name != "nt":
                self.assertEqual(destination.stat().st_mode & 0o777, 0o700)
                self.assertEqual((destination / "capture.json").stat().st_mode & 0o777, 0o600)
            else:
                acl = subprocess.run(["icacls", str(destination)], capture_output=True, text=True, check=True)
                self.assertNotIn("(I)", acl.stdout)

    def test_existing_output_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "bundle"
            evidence.write_bundle(self.capture, destination)
            before = (destination / "capture.json").read_bytes()
            with self.assertRaisesRegex(evidence.CaptureFailure, "already exists"):
                evidence.write_bundle(self.capture, destination)
            self.assertEqual((destination / "capture.json").read_bytes(), before)

    def test_existing_empty_directory_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "bundle"
            destination.mkdir()
            with self.assertRaisesRegex(evidence.CaptureFailure, "already exists"):
                evidence.write_bundle(self.capture, destination)
            self.assertEqual(list(destination.iterdir()), [])

    def test_racing_empty_destination_is_not_overwritten(self) -> None:
        real_finalize = evidence.finalize_directory
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "bundle"
            def race(staging: Path, target: Path) -> None:
                target.mkdir()
                real_finalize(staging, target)
            with patch.object(evidence, "finalize_directory", side_effect=race):
                with self.assertRaises(evidence.CaptureFailure):
                    evidence.write_bundle(self.capture, destination)
            self.assertEqual(list(destination.iterdir()), [])

    def test_failed_finalization_does_not_leave_partial_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "bundle"
            with patch.object(evidence, "finalize_directory", side_effect=OSError("synthetic failure")):
                with self.assertRaisesRegex(evidence.CaptureFailure, "atomic output finalization failed"):
                    evidence.write_bundle(self.capture, destination)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_traversal_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(evidence.CaptureFailure, "traversal"):
            evidence.safe_path(Path("parent") / ".." / "target")

    def test_junction_or_symlink_ancestor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            link = Path(directory) / "link"
            if os.name == "nt":
                env = dict(os.environ, EVAXIS_TEST_LINK=str(link), EVAXIS_TEST_TARGET=str(target))
                subprocess.run(
                    ["pwsh", "-NoProfile", "-NonInteractive", "-Command",
                     "New-Item -ItemType Junction -Path $env:EVAXIS_TEST_LINK -Target $env:EVAXIS_TEST_TARGET -ErrorAction Stop | Out-Null"],
                    env=env, capture_output=True, check=True,
                )
            else:
                link.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(evidence.CaptureFailure, "symlink or reparse"):
                evidence.safe_path(link / "new-bundle", must_exist=False)

    def test_diagnostic_cli_does_not_print_source_content(self) -> None:
        self.capture["observations"][0]["record"]["representation"]["content"]["sensitiveValue"] = "synthetic-sensitive-content-never-log"
        self.capture["observations"][0]["record"]["observedAt"] = "invalid"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            source.write_text(json.dumps(self.capture), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(ROOT / "capture" / "package.py"), "validate-capture", "--input", str(source)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("synthetic-sensitive-content-never-log", result.stdout + result.stderr)

    def test_fresh_offline_invocation_without_maester(self) -> None:
        self.run_example(unknown=False)

    def test_fresh_unknown_inventory_invocation_without_maester(self) -> None:
        self.run_example(unknown=True)

    def run_example(self, *, unknown: bool) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            command = [
                "pwsh", "-NoProfile", "-File", str(ROOT / "examples" / "evidence-preservation" / "Invoke-OfflineExample.ps1"),
                "-OutputDirectory", str(output), "-PythonCommand", sys.executable,
            ]
            if unknown:
                command.extend(["-InventoryStatus", "unknown"])
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stderr)
            package = evidence.read_json(output / "package.json")
            self.assertEqual(evidence.validate_evidence_package(package)["observations"], 2)
            self.assertEqual(package["manifest"]["coverage"]["status"], "unknown" if unknown else "partial")


class MaesterDependent(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("EVAXIS_MAESTER_SOURCE"), "set EVAXIS_MAESTER_SOURCE to the pinned Maester lab checkout")
    def test_actual_native_capture_and_result_association(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            result = subprocess.run(
                ["pwsh", "-NoProfile", "-File", str(ROOT / "integrations" / "maester" / "Invoke-SyntheticMaester.ps1"),
                 "-MaesterSourcePath", os.environ["EVAXIS_MAESTER_SOURCE"],
                 "-OutputDirectory", str(output), "-PythonCommand", sys.executable],
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
                capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            package = evidence.read_json(output / "package.json")
            self.assertEqual(evidence.validate_evidence_package(package)["assessments"], 3)
            associations = [record["extensions"][evidence.EXTENSION]["frameworkAssociation"] for record in package["assessments"]]
            self.assertEqual([item["resultClaim"] for item in associations], ["Passed", "Failed", "Skipped"])
            self.assertEqual(len({item["invocationId"] for item in associations}), 3)
            self.assertEqual({item["collectionRunId"] for item in associations}, {package["envelope"]["collectionRunId"]})


if __name__ == "__main__":
    unittest.main()
