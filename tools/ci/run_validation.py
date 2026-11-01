#!/usr/bin/env python3
"""Run the existing synthetic suites with mandatory native execution."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from prepare_validation import PreparationFailure, read_manifest, verify_prepared

ROOT = Path(__file__).resolve().parents[2]
NATIVE_TEST = "test_capture.MaesterDependent.test_actual_native_capture_and_result_association"
PLATFORM_SKIP_REASONS = {
    "Linux descriptor/no-replace cases require a real Linux runner",
    "Windows handle/reparse/drive cases require a real Windows runner",
}


class RequiredNativeResult(unittest.TextTestResult):
    native_started: bool = False

    def startTest(self, test: unittest.TestCase) -> None:
        if test.id() == NATIVE_TEST:
            self.native_started = True
        super().startTest(test)


def command(arguments: list[str]) -> str:
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=180)
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        raise RuntimeError("validation command failed")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    report: dict[str, Any] = {
        "format": "evaxis.synthetic-validation/0.1",
        "status": "failed",
        "commit": os.environ.get("GITHUB_SHA"),
        "runner": os.environ.get("RUNNER_OS", platform.system()),
        "runnerImage": os.environ.get("ImageOS"),
        "runnerImageVersion": os.environ.get("ImageVersion"),
        "python": platform.python_version(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "receiverVerification": "not-performed",
        "sourceTruth": "not-established",
        "tenantAccess": "not-performed",
    }
    temporary: Path | None = None
    try:
        verify_prepared(args.workspace, read_manifest())
        pwsh = shutil.which("pwsh")
        if pwsh is None:
            raise RuntimeError("PowerShell 7.4+ is required")
        os.environ["PSModulePath"] = os.pathsep.join([
            str(args.workspace / "modules"), str(Path(pwsh).resolve().parent / "Modules"),
        ])
        os.environ["EVAXIS_MAESTER_SOURCE"] = str(args.workspace / "maester")
        os.environ["MAESTER_DISABLE_TELEMETRY"] = "1"
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        temporary = Path(tempfile.mkdtemp(prefix="validation-tests-", dir=args.workspace))
        for key in ("TEMP", "TMP", "TMPDIR"):
            os.environ[key] = str(temporary)
        tempfile.tempdir = None
        report["powershell"] = command([pwsh, "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]).strip()
        if sys.platform == "linux":
            report["filesystem"] = command(["stat", "-f", "-c", "%T", str(temporary)]).strip()
        elif os.name == "nt":
            report["filesystem"] = command([
                pwsh, "-NoProfile", "-Command",
                "([IO.DriveInfo]::new([IO.Path]::GetPathRoot($env:TEMP))).DriveFormat",
            ]).strip()
        else:
            raise RuntimeError("publication validation supports only Windows and Linux")
        report["conformance"] = command([sys.executable, "-B", str(ROOT / "tools" / "validate_conformance.py")]).strip()
        suite = unittest.defaultTestLoader.discover(str(ROOT / "tests" / "capture"), pattern="test_*.py")
        result = unittest.TextTestRunner(verbosity=2, resultclass=RequiredNativeResult).run(suite)
        report["pythonTests"] = {
            "run": result.testsRun, "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": [{"test": test.id(), "reason": reason} for test, reason in result.skipped],
        }
        unexpected = [(test, reason) for test, reason in result.skipped if reason not in PLATFORM_SKIP_REASONS]
        native_skipped = any(test.id() == NATIVE_TEST for test, _ in result.skipped)
        if not result.wasSuccessful() or unexpected or native_skipped or not result.native_started:
            raise RuntimeError("capture suite failed or required execution was skipped")
        report["nativeIntegration"] = "passed: actual callback; two observations; three Passed/Failed/Skipped assessments"
        script = str(ROOT / "tests" / "capture" / "Test-Capture.ps1")
        os.environ["EVAXIS_CAPTURE_TEST_SCRIPT"] = script
        output = command([
            pwsh, "-NoProfile", "-Command",
            "$ErrorActionPreference = 'Stop'; & $env:EVAXIS_CAPTURE_TEST_SCRIPT | ConvertTo-Json -Compress",
        ])
        report["powershellTests"] = json.loads(output)
        if report["powershellTests"]["Failed"] != 0:
            raise RuntimeError("PowerShell capture suite failed")
        report["status"] = "passed"
    except (PreparationFailure, RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        report["failure"] = str(exc) if isinstance(exc, (PreparationFailure, RuntimeError)) else "validation execution failed"
        print(report["failure"], file=sys.stderr)
    finally:
        if temporary is not None:
            try:
                temporary.rmdir()
            except OSError:
                report["status"] = "failed"
                report["failure"] = "validation temporary cleanup failed"
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
