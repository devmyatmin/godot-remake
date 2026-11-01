"""Bounded, read-only discovery for Unity project layouts and text metadata."""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

MAX_FILES = 5000
MAX_TEXT_BYTES = 128 * 1024
MAX_BINARY_LIST = 100
GUID_RE = re.compile(rb"(?m)^guid:\s*([0-9a-fA-F]{32})\s*$")
YAML_OBJECT_RE = re.compile(rb"(?m)^--- !u!(\d+) ")
UNITY_BINARY_EXTENSIONS = {".assets", ".bundle", ".unity3d", ".ress", ".resource", ".resS"}


def _read_limited(path: Path, limit: int = MAX_TEXT_BYTES) -> bytes:
    with path.open("rb") as handle:
        return handle.read(limit)


def inspect_unity_project(project_root: Path, max_files: int = 3000) -> dict[str, Any]:
    """Inspect project markers and bounded metadata; never modifies source files."""
    if not isinstance(max_files, int) or isinstance(max_files, bool) or not 1 <= max_files <= MAX_FILES:
        raise ValueError(f"max_files must be between 1 and {MAX_FILES}")
    root = project_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Unity project path must be a directory")

    markers = []
    for marker in (
        "Assets", "Packages", "ProjectSettings", "ProjectSettings/ProjectVersion.txt",
        "Packages/manifest.json", "ProjectSettings/ProjectSettings.asset",
    ):
        if (root / marker).exists():
            markers.append(marker)

    version = None
    version_file = root / "ProjectSettings" / "ProjectVersion.txt"
    if version_file.is_file() and not version_file.is_symlink():
        match = re.search(r"(?m)^m_EditorVersion:\s*(.+?)\s*$", _read_limited(version_file).decode("utf-8", "replace"))
        if match:
            version = match.group(1)

    packages: dict[str, str] = {}
    manifest = root / "Packages" / "manifest.json"
    if manifest.is_file() and not manifest.is_symlink():
        try:
            data = json.loads(_read_limited(manifest).decode("utf-8"))
            dependencies = data.get("dependencies", {}) if isinstance(data, dict) else {}
            if isinstance(dependencies, dict):
                packages = {
                    str(name): str(value)
                    for name, value in list(dependencies.items())[:500]
                    if isinstance(name, str) and isinstance(value, (str, int, float))
                }
        except (UnicodeDecodeError, json.JSONDecodeError, OSError):
            packages = {}

    extension_counts: Counter[str] = Counter()
    guid_counts: Counter[str] = Counter()
    yaml_object_counts: Counter[str] = Counter()
    binary_assets: list[dict[str, Any]] = []
    scanned = 0
    text_files_sampled = 0
    truncated = False
    assets_root = root / "Assets"

    if assets_root.is_dir() and not assets_root.is_symlink():
        for current, dirs, files in os.walk(assets_root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not (Path(current) / d).is_symlink())
            for filename in sorted(files):
                file_path = Path(current) / filename
                if file_path.is_symlink():
                    continue
                try:
                    if not file_path.is_file():
                        continue
                    scanned += 1
                    if scanned > max_files:
                        truncated = True
                        break
                    ext = file_path.suffix.lower() or "[no extension]"
                    extension_counts[ext] += 1
                    if filename.endswith(".meta"):
                        try:
                            for guid in GUID_RE.findall(_read_limited(file_path)):
                                guid_counts[guid.decode("ascii").lower()] += 1
                            text_files_sampled += 1
                        except OSError:
                            pass
                    elif ext in {".unity", ".prefab", ".asset"}:
                        try:
                            raw = _read_limited(file_path)
                            for class_id in YAML_OBJECT_RE.findall(raw):
                                yaml_object_counts[class_id.decode("ascii")] += 1
                            text_files_sampled += 1
                        except OSError:
                            pass
                    elif ext in UNITY_BINARY_EXTENSIONS and len(binary_assets) < MAX_BINARY_LIST:
                        try:
                            binary_assets.append({
                                "path": file_path.relative_to(root).as_posix(),
                                "extension": ext,
                                "size_bytes": file_path.stat(follow_symlinks=False).st_size,
                                "inspection": "metadata_only_not_decoded",
                            })
                        except OSError:
                            pass
            if truncated:
                break

    duplicate_guids = sorted(guid for guid, count in guid_counts.items() if count > 1)
    return {
        "is_unity_project": bool({"Assets", "ProjectSettings", "Packages"} & set(markers)),
        "markers_found": markers,
        "unity_editor_version": version,
        "package_dependency_count": len(packages),
        "packages": packages,
        "assets_file_count": min(scanned, max_files),
        "assets_scan_truncated": truncated,
        "extension_counts": dict(sorted(extension_counts.items())),
        "text_metadata_files_sampled": text_files_sampled,
        "unique_meta_guid_count": len(guid_counts),
        "duplicate_meta_guids": duplicate_guids[:100],
        "yaml_object_class_id_counts": dict(sorted(yaml_object_counts.items())),
        "binary_unity_assets": binary_assets,
        "support_level": "partial_metadata_inspection",
        "limitations": [
            "Unity binary serialized objects and AssetBundles are listed but not decoded by this first inspector.",
            "Text YAML parsing is limited to object class IDs; complete object/reference conversion is a later importer stage.",
            "Only bounded samples of .meta, .unity, .prefab, and .asset text are inspected.",
        ],
    }
