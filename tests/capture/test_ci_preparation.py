"""Credential-free integrity/path tests for the synthetic CI prerequisites."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.ci import prepare_validation as preparation  # noqa: E402


def archive_bytes(extra: str | zipfile.ZipInfo | None = None) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("Microsoft.Graph.Authentication.psd1", "synthetic-not-executed")
        if extra is not None:
            archive.writestr(extra, "synthetic-not-executed")
    data = stream.getvalue()
    if isinstance(extra, str) and "\\" in extra:
        # Windows ZipInfo normalizes separators; retain the hostile raw header.
        data = data.replace(extra.replace("\\", "/").encode(), extra.encode())
    return data


class PrerequisiteIntegrity(unittest.TestCase):
    def test_reviewed_manifest_is_complete(self) -> None:
        manifest = preparation.read_manifest()
        self.assertEqual(manifest["maester"]["trackedModuleFiles"], 752)
        self.assertEqual(manifest["graphAuthentication"]["version"], "2.27.0")

    def test_malformed_or_foreign_manifest_is_refused(self) -> None:
        valid = preparation.read_manifest()
        foreign = copy.deepcopy(valid)
        foreign["graphAuthentication"]["uri"] = "https://invalid.example/unreviewed"
        for value in ([], {"format": "unknown"}, foreign):
            with self.subTest(value=type(value).__name__), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                with patch.object(preparation, "MANIFEST", path):
                    with self.assertRaises(preparation.PreparationFailure):
                        preparation.read_manifest()

    def test_checksum_tamper_is_refused_before_extraction_or_git(self) -> None:
        data = archive_bytes()
        manifest = preparation.read_manifest()
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "new"
            with patch.object(preparation.urllib.request, "urlopen", return_value=io.BytesIO(data)):
                with patch.object(preparation, "git") as git:
                    with self.assertRaisesRegex(preparation.PreparationFailure, "checksum mismatch"):
                        preparation.prepare(workspace, manifest)
            git.assert_not_called()
            self.assertEqual(list(workspace.iterdir()), [])

    def test_archive_traversal_stream_absolute_and_duplicate_paths_are_refused(self) -> None:
        for name in ("../outside", "/absolute", "folder\\outside", "file:stream",
                     "folder./file", "MICROSOFT.GRAPH.AUTHENTICATION.PSD1"):
            with self.subTest(name=name):
                data = archive_bytes(name)
                with self.assertRaises(preparation.PreparationFailure):
                    preparation.checked_archive(data, hashlib.sha256(data).hexdigest())

    def test_archive_symlink_is_refused(self) -> None:
        link = zipfile.ZipInfo("linked")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        data = archive_bytes(link)
        with self.assertRaisesRegex(preparation.PreparationFailure, "linked"):
            preparation.checked_archive(data, hashlib.sha256(data).hexdigest())

    def test_archive_expansion_limit_is_enforced(self) -> None:
        data = archive_bytes()
        with patch.object(preparation, "MAX_EXPANDED", 1):
            with self.assertRaisesRegex(preparation.PreparationFailure, "exceeds limits"):
                preparation.checked_archive(data, hashlib.sha256(data).hexdigest())

    def test_valid_synthetic_archive_is_read_without_execution(self) -> None:
        data = archive_bytes("lib/synthetic.dll")
        with preparation.checked_archive(data, hashlib.sha256(data).hexdigest()) as archive:
            self.assertEqual(archive.read("lib/synthetic.dll"), b"synthetic-not-executed")

    def test_native_tree_checksum_binds_actual_file_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            module = source / "powershell"
            module.mkdir()
            file = module / "test.psm1"
            file.write_bytes(b"synthetic-original")
            with patch.object(preparation, "git", return_value=b"powershell/test.psm1\0"):
                before, count = preparation.module_tree(source)
                file.write_bytes(b"synthetic-substitution")
                after, changed_count = preparation.module_tree(source)
            self.assertNotEqual(before, after)
            self.assertEqual((count, changed_count), (1, 1))

    def test_extracted_graph_tamper_is_refused_before_execution(self) -> None:
        manifest = preparation.read_manifest()
        data = archive_bytes()
        manifest["graphAuthentication"]["sha256"] = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "graph.nupkg").write_bytes(data)
            module = workspace / "modules" / "Microsoft.Graph.Authentication" / "2.27.0"
            module.mkdir(parents=True)
            (module / "Microsoft.Graph.Authentication.psd1").write_text("tampered", encoding="utf-8")
            def git(source: Path, *arguments: str) -> bytes:
                return manifest["maester"]["commit"].encode() if arguments[0] == "rev-parse" else b""
            with patch.object(preparation, "git", side_effect=git):
                with patch.object(preparation, "module_tree", return_value=(
                    manifest["maester"]["moduleTreeSha256"], manifest["maester"]["trackedModuleFiles"],
                )):
                    with self.assertRaisesRegex(preparation.PreparationFailure, "extracted Graph"):
                        preparation.verify_prepared(workspace, manifest)
