#!/usr/bin/env python3
"""Fetch and verify only the reviewed, public synthetic-test prerequisites."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("native-dependencies.json")
MAX_DOWNLOAD = 64_000_000
MAX_EXPANDED = 128_000_000


class PreparationFailure(Exception):
    """A bounded prerequisite failure, without downloaded content."""


def read_manifest() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or set(manifest) != {"format", "maester", "graphAuthentication"} or (
        manifest.get("format") != "evaxis.synthetic-ci-dependencies/0.1"
    ):
        raise PreparationFailure("unsupported prerequisite manifest")
    maester, graph = manifest["maester"], manifest["graphAuthentication"]
    if not isinstance(maester, dict) or not isinstance(graph, dict) or set(maester) != {
        "repository", "commit", "moduleVersion", "moduleTreeSha256", "trackedModuleFiles",
    } or set(graph) != {"version", "uri", "sha256"}:
        raise PreparationFailure("malformed prerequisite manifest")
    if maester["repository"] != "https://github.com/maester365/maester" or (
        maester["commit"] != "b8ad89557a831d3d3d7c369174300701243af8a6"
    ) or maester["moduleVersion"] != "3.0.0" or graph["version"] != "2.27.0" or (
        graph["uri"] != "https://www.powershellgallery.com/api/v2/package/Microsoft.Graph.Authentication/2.27.0"
    ):
        raise PreparationFailure("prerequisites must match the reviewed native experiment")
    for digest in (maester["moduleTreeSha256"], graph["sha256"]):
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise PreparationFailure("prerequisite integrity pin is missing or malformed")
    if maester["trackedModuleFiles"] != 752:
        raise PreparationFailure("unexpected native module inventory")
    return manifest


def archive_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or "\\" in name or ":" in name or any(
        part in {"", ".", ".."} or part.rstrip(" .") != part for part in name.rstrip("/").split("/")
    ):
        raise PreparationFailure("unsafe prerequisite archive path")
    return path


def regular_path(path: Path, root: Path) -> None:
    for component in (path, *path.parents):
        if component == root:
            break
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise PreparationFailure("linked prerequisite path")
    if not stat.S_ISREG(path.lstat().st_mode):
        raise PreparationFailure("prerequisite content must be a regular file")


def checked_archive(data: bytes, expected: str) -> zipfile.ZipFile:
    if len(data) > MAX_DOWNLOAD or hashlib.sha256(data).hexdigest() != expected:
        raise PreparationFailure("Graph prerequisite checksum mismatch")
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        entries = archive.infolist()
        if len(entries) > 1000 or sum(item.file_size for item in entries) > MAX_EXPANDED:
            raise PreparationFailure("prerequisite archive exceeds limits")
        names = set()
        for item in entries:
            archive_path(item.orig_filename)
            if item.orig_filename != item.filename:
                raise PreparationFailure("unsafe prerequisite archive path normalization")
            name = str(archive_path(item.filename)).casefold()
            mode = item.external_attr >> 16
            if name in names or stat.S_ISLNK(mode) or item.flag_bits & 1:
                raise PreparationFailure("duplicate, linked or encrypted prerequisite archive entry")
            names.add(name)
        if "microsoft.graph.authentication.psd1" not in names or archive.testzip() is not None:
            raise PreparationFailure("Graph prerequisite archive is incomplete")
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise PreparationFailure("invalid prerequisite archive") from exc
    return archive


def git(source: Path, *arguments: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "-c", "credential.helper=", "-c", "core.autocrlf=false",
             "-c", "core.hooksPath=" + str(source / ".disabled-hooks"),
             "-C", str(source), *arguments],
            capture_output=True, check=True, timeout=120,
            env=dict(os.environ, GIT_TERMINAL_PROMPT="0"),
        ).stdout
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise PreparationFailure("pinned source Git operation failed") from exc


def module_tree(source: Path) -> tuple[str, int]:
    paths = sorted(path for path in git(source, "ls-files", "-z", "--", "powershell").split(b"\0") if path)
    digest = hashlib.sha256()
    total = 0
    if len(paths) > 1000:
        raise PreparationFailure("native module inventory exceeds limits")
    for name in paths:
        relative = archive_path(name.decode("utf-8"))
        path = source.joinpath(*relative.parts)
        regular_path(path, source)
        data = path.read_bytes()
        total += len(data)
        if total > MAX_EXPANDED:
            raise PreparationFailure("native module content exceeds limits")
        digest.update(name + b"\0" + hashlib.sha256(data).digest())
    return digest.hexdigest(), len(paths)


def verify_prepared(workspace: Path, manifest: dict[str, Any]) -> None:
    source = workspace / "maester"
    pin = manifest["maester"]
    if git(source, "rev-parse", "HEAD").decode().strip() != pin["commit"] or (
        git(source, "status", "--porcelain", "--untracked-files=all").strip()
    ):
        raise PreparationFailure("native source is modified or at the wrong commit")
    if module_tree(source) != (pin["moduleTreeSha256"], pin["trackedModuleFiles"]):
        raise PreparationFailure("native executable module checksum mismatch")
    graph = manifest["graphAuthentication"]
    module = workspace / "modules" / "Microsoft.Graph.Authentication" / graph["version"]
    expected_files = set()
    with checked_archive((workspace / "graph.nupkg").read_bytes(), graph["sha256"]) as archive:
        for item in archive.infolist():
            if not item.is_dir():
                path = module.joinpath(*archive_path(item.filename).parts)
                regular_path(path, workspace)
                expected_files.add(path.relative_to(module).as_posix())
                if path.read_bytes() != archive.read(item):
                    raise PreparationFailure("extracted Graph prerequisite checksum mismatch")
    actual_files = set()
    for path in module.rglob("*"):
        if path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & 0x400:
            raise PreparationFailure("linked prerequisite path")
        if path.is_file():
            actual_files.add(path.relative_to(module).as_posix())
    if actual_files != expected_files:
        raise PreparationFailure("unexpected extracted Graph prerequisite content")


def prepare(workspace: Path, manifest: dict[str, Any]) -> None:
    workspace = Path(os.path.abspath(workspace))
    for component in (*reversed(workspace.parents), workspace):
        if component.exists():
            info = component.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise PreparationFailure("prerequisite workspace must not traverse linked paths")
    if workspace == ROOT or ROOT in workspace.parents:
        raise PreparationFailure("prerequisites must stay outside the Core checkout")
    workspace.mkdir(mode=0o700)
    graph = manifest["graphAuthentication"]
    try:
        with urllib.request.urlopen(graph["uri"], timeout=60) as response:
            data = response.read(MAX_DOWNLOAD + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise PreparationFailure("public Graph prerequisite download failed") from exc
    with checked_archive(data, graph["sha256"]) as archive:
        module = workspace / "modules" / "Microsoft.Graph.Authentication" / graph["version"]
        module.mkdir(parents=True, mode=0o700)
        for item in archive.infolist():
            destination = module.joinpath(*archive_path(item.filename).parts)
            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True, mode=0o700)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with destination.open("xb") as stream:
                    stream.write(archive.read(item))
    (workspace / "graph.nupkg").write_bytes(data)
    source = workspace / "maester"
    source.mkdir(mode=0o700)
    git(source, "init", "--quiet")
    git(source, "config", "core.autocrlf", "false")
    git(source, "remote", "add", "origin", manifest["maester"]["repository"])
    git(source, "fetch", "--quiet", "--depth=1", "origin", manifest["maester"]["commit"])
    git(source, "checkout", "--quiet", "--detach", "FETCH_HEAD")
    verify_prepared(workspace, manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args()
    try:
        prepare(args.workspace, read_manifest())
    except (PreparationFailure, OSError, ValueError, KeyError) as exc:
        message = str(exc) if isinstance(exc, PreparationFailure) else "cannot prepare prerequisite workspace"
        print("prerequisite preparation failed: " + message, file=sys.stderr)
        return 1
    print("reviewed native prerequisites downloaded and checksum-verified; no module executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
