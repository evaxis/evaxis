"""Offline regressions for the fail-closed four-configuration merge gate."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.ci import check_validation_gate as gate  # noqa: E402

COMMIT = "a" * 40


def report(runner: str, version: str) -> dict:
    return {
        "format": "evaxis.synthetic-validation/0.1", "status": "passed", "commit": COMMIT,
        "runner": "Windows" if runner == "windows-2025" else "Linux", "python": version + ".1",
        "nativeIntegration": gate.NATIVE_RESULT, "receiverVerification": "not-performed",
        "sourceTruth": "not-established", "tenantAccess": "not-performed",
        "conformance": "schema and fixture-data checks passed: synthetic",
        "pythonTests": {"run": 130, "failures": 0, "errors": 0, "skipped": []},
        "powershellTests": {"PowerShellCaptureTests": 36, "Failed": 0},
    }


def prepare(root: Path) -> list[Path]:
    paths = []
    for name, (runner, version) in gate.CONFIGURATIONS.items():
        directory = root / name
        directory.mkdir()
        path = directory / "validation-report.json"
        path.write_text(json.dumps(report(runner, version)), encoding="utf-8")
        paths.append(path)
    return paths


class ValidationGate(unittest.TestCase):
    def test_all_four_successful_reports_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare(root)
            gate.check_gate("success", root, COMMIT)

    def test_non_success_matrix_fails_even_with_successful_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare(root)
            for result in ("failure", "cancelled", "skipped", "neutral", "", "missing"):
                with self.subTest(result=result), self.assertRaises(gate.GateFailure):
                    gate.check_gate(result, root, COMMIT)

    def test_each_missing_matrix_report_fails(self) -> None:
        for missing in gate.CONFIGURATIONS:
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                paths = prepare(root)
                next(path for path in paths if path.parent.name == missing).unlink()
                with self.assertRaises(gate.GateFailure):
                    gate.check_gate("success", root, COMMIT)

    def test_missing_matrix_job_directory_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = prepare(root)
            paths[0].unlink()
            paths[0].parent.rmdir()
            with self.assertRaises(gate.GateFailure):
                gate.check_gate("success", root, COMMIT)

    def test_failed_cancelled_skipped_neutral_report_fails(self) -> None:
        for status in ("failed", "cancelled", "skipped", "neutral"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = prepare(root)[0]
                value = json.loads(path.read_text(encoding="utf-8"))
                value["status"] = status
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(gate.GateFailure):
                    gate.check_gate("success", root, COMMIT)

    def test_stale_or_native_unexecuted_report_fails(self) -> None:
        for field, value in (("commit", "b" * 40), ("nativeIntegration", "skipped"),
                             ("receiverVerification", "verified"), ("sourceTruth", "established")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = prepare(root)[0]
                document = json.loads(path.read_text(encoding="utf-8"))
                document[field] = value
                path.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaises(gate.GateFailure):
                    gate.check_gate("success", root, COMMIT)

    def test_malformed_or_unexpected_report_fails_without_payload_diagnostic(self) -> None:
        for value in ("synthetic-sensitive-never-log", "[]"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                prepare(root)[0].write_text(value, encoding="utf-8")
                with self.assertRaises(gate.GateFailure) as caught:
                    gate.check_gate("success", root, COMMIT)
                self.assertNotIn("synthetic-sensitive-never-log", str(caught.exception))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare(root)
            (root / "extra").mkdir()
            with self.assertRaises(gate.GateFailure):
                gate.check_gate("success", root, COMMIT)

    def test_suite_failure_or_native_skip_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = prepare(root)[0]
            baseline = json.loads(path.read_text(encoding="utf-8"))
            for field, value in (("failures", 1), ("errors", 1), ("run", 0),
                                 ("skipped", [{"test": "test_capture.MaesterDependent.test_actual_native_capture_and_result_association",
                                               "reason": "not configured"}])):
                with self.subTest(field=field):
                    modified = json.loads(json.dumps(baseline))
                    modified["pythonTests"][field] = value
                    path.write_text(json.dumps(modified), encoding="utf-8")
                    with self.assertRaises(gate.GateFailure):
                        gate.check_gate("success", root, COMMIT)

    def test_opposite_platform_skips_are_explicitly_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in prepare(root):
                value = json.loads(path.read_text(encoding="utf-8"))
                opposite = "Linux" if value["runner"] == "Windows" else "Windows"
                reason = ("Linux descriptor/no-replace cases require a real Linux runner" if opposite == "Linux"
                          else "Windows handle/reparse/drive cases require a real Windows runner")
                value["pythonTests"]["skipped"] = [{
                    "test": f"test_capture.{opposite}Filesystem.synthetic", "reason": reason,
                }]
                path.write_text(json.dumps(value), encoding="utf-8")
            gate.check_gate("success", root, COMMIT)
