#!/usr/bin/env python3
"""Fail the merge gate unless the complete matrix actually succeeded."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CONFIGURATIONS = {
    f"validation-{runner}-python-{version}": (runner, version)
    for runner in ("windows-2025", "ubuntu-24.04")
    for version in ("3.11", "3.13")
}
NATIVE_RESULT = "passed: actual callback; two observations; three Passed/Failed/Skipped assessments"


class GateFailure(Exception):
    """A fixed diagnostic, never report payloads or filesystem paths."""


def check_gate(result: str, reports: Path, commit: str) -> None:
    if result != "success":
        raise GateFailure("capture matrix did not conclude success")
    if not commit or not reports.is_dir() or {path.name for path in reports.iterdir()} != set(CONFIGURATIONS):
        raise GateFailure("the four required capture reports are missing or unexpected")
    for name, (runner, version) in CONFIGURATIONS.items():
        path = reports / name / "validation-report.json"
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
            raise GateFailure("required capture report is absent or invalid")
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise GateFailure("required capture report cannot be decoded") from exc
        if not isinstance(report, dict):
            raise GateFailure("required capture report has invalid shape")
        if (report.get("format") != "evaxis.synthetic-validation/0.1" or
                report.get("status") != "passed" or report.get("commit") != commit or
                report.get("nativeIntegration") != NATIVE_RESULT or
                report.get("receiverVerification") != "not-performed" or
                report.get("sourceTruth") != "not-established" or
                report.get("tenantAccess") != "not-performed" or
                report.get("runner") != ("Windows" if runner == "windows-2025" else "Linux") or
                not isinstance(report.get("python"), str) or
                not report["python"].startswith(version + ".") or
                not isinstance(report.get("conformance"), str) or
                not report["conformance"].startswith("schema and fixture-data checks passed:")):
            raise GateFailure("required capture execution or trust result was not established")
        python = report.get("pythonTests")
        powershell = report.get("powershellTests")
        if (not isinstance(python, dict) or not isinstance(powershell, dict) or
                type(python.get("run")) is not int or python["run"] < 130 or
                python.get("failures") != 0 or python.get("errors") != 0 or
                not isinstance(python.get("skipped"), list) or
                type(powershell.get("PowerShellCaptureTests")) is not int or
                powershell["PowerShellCaptureTests"] < 36 or powershell.get("Failed") != 0):
            raise GateFailure("required capture suites did not execute successfully")
        opposite = "Linux" if runner == "windows-2025" else "Windows"
        reason = ("Linux descriptor/no-replace cases require a real Linux runner" if opposite == "Linux"
                  else "Windows handle/reparse/drive cases require a real Windows runner")
        for skipped in python["skipped"]:
            if (not isinstance(skipped, dict) or skipped.get("reason") != reason or
                    not isinstance(skipped.get("test"), str) or
                    not skipped["test"].startswith(f"test_capture.{opposite}Filesystem.")):
                raise GateFailure("required capture execution was unexpectedly skipped")
        if python["run"] <= len(python["skipped"]):
            raise GateFailure("required capture cases did not execute")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True)
    parser.add_argument("--reports", required=True, type=Path)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    try:
        check_gate(args.result, args.reports, args.commit)
    except (GateFailure, OSError) as exc:
        print(str(exc) if isinstance(exc, GateFailure) else "cannot inspect capture reports", file=sys.stderr)
        return 1
    print("all four capture configurations and required native execution passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
