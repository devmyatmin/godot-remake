"""Bounded, read-only discovery and partial text-metadata extraction for Unity projects."""
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
MAX_EXTRACTED_REFERENCES = 1000
GUID_RE = re.compile(rb"(?m)^guid:\\s*([0-9a-fA-F]{32})\\s*$")
YAML_OBJECT_RE = re.compile(rb"(?m)^--- !u!(\\d+) &(-?\\d+)")
YAML_PPTR_RE = re.compile(
    rb"\\{fileID:\\s*(-?\\d+)(?:,\\s*guid:\\s*([0-9a-fA-F]{32}))?(?:,\\s*type:\\s*\\d+)?\\}"
)
UNITY_BINARY_EXTENSIONS = {".assets", ".bundle", ".unity3d", ".ress", ".resource", ".resS"}


def _read_limited(path: Path, limit: int = MAX_TEXT_BYTES) -> bytes:
    with path.open("rb") as handle:
        return handle.read(limit)


def inspect_unity_project(project_root: Path, max_files: int = 3000) -> dict[str, Any]:
    """Inspect Unity markers, GUIDs, YAML object IDs and references without modifying source."""
    if not isinstance(max_files, int) or isinstance(max_files, bool) or not 1 <= max_files <= MAX_FILES:
        raise ValueError(f"max_files must be between 1 and {MAX_FILES}")
    root = project_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Unity project path must be a directory")

    markers = []
    for marker in (
        "Assets", "Packages", "ProjectSettings", "ProjectSettings/ProjectVersion.txt",
        "Packages/manifest.json", "Packages/packages-lock.json",
        "ProjectSettings/ProjectSettings.asset",
    ):
        if (root / marker).exists():
            markers.append(marker)

    version = None
    version_file = root / "ProjectSettings" / "ProjectVersion.txt"
    if version_file.is_file() and not version_file.is_symlink():
        match = re.search(r"(?m)^m_EditorVersion:\\s*(.+?)\\s*$", _read_limited(version_file).decode("utf-8", "replace"))
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
    guid_to_asset: dict[str, str] = {}
    duplicate_guid_counts: Counter[str] = Counter()
    yaml_class_counts: Counter[str] = Counter()
    yaml_object_ids: list[dict[str, Any]] = []
    yaml_references: list[dict[str, Any]] = []
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
                            raw = _read_limited(file_path)
                            matches = GUID_RE.findall(raw)
                            if matches:
                                guid = matches[0].decode("ascii").lower()
                                duplicate_guid_counts[guid] += 1
                                asset_path = file_path.with_suffix("").relative_to(root).as_posix()
                                guid_to_asset.setdefault(guid, asset_path)
                            text_files_sampled += 1
                        except OSError:
                            pass
                    elif ext in {".unity", ".prefab", ".asset"}:
                        try:
                            raw = _read_limited(file_path)
                            for class_id, object_id in YAML_OBJECT_RE.findall(raw):
                                class_text = class_id.decode("ascii")
                                yaml_class_counts[class_text] += 1
                                if len(yaml_object_ids) < MAX_EXTRACTED_REFERENCES:
                                    yaml_object_ids.append({
                                        "source": file_path.relative_to(root).as_posix(),
                                        "class_id": int(class_text),
                                        "file_id": int(object_id.decode("ascii")),
                                    })
                            for file_id, guid in YAML_PPTR_RE.findall(raw):
                                if len(yaml_references) >= MAX_EXTRACTED_REFERENCES:
                                    break
                                guid_text = guid.decode("ascii").lower() if guid else None
                                yaml_references.append({
                                    "source": file_path.relative_to(root).as_posix(),
                                    "file_id": int(file_id.decode("ascii")),
                                    "guid": guid_text,
                                    "resolved_asset": guid_to_asset.get(guid_text) if guid_text else None,
                                    "resolution": (
                                        "resolved" if guid_text in guid_to_asset else
                                        "unresolved_external_or_not_yet_indexed" if guid_text else
                                        "local_file_id_reference"
                                    ),
                                })
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
                except OSError:
                    continue
            if truncated:
                break

    duplicate_guids = sorted(guid for guid, count in duplicate_guid_counts.items() if count > 1)
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
        "unique_meta_guid_count": len(guid_to_asset),
        "guid_to_asset": dict(sorted(guid_to_asset.items())),
        "duplicate_meta_guids": duplicate_guids[:100],
        "yaml_object_class_id_counts": dict(sorted(yaml_class_counts.items())),
        "yaml_objects": yaml_object_ids,
        "yaml_references": yaml_references,
        "binary_unity_assets": binary_assets,
        "support_matrix": {
            "project_layout_and_packages": "supported",
            "meta_guid_inventory": "supported",
            "text_yaml_object_ids_and_pptr_references": "partial",
            "binary_serialized_assets_and_assetbundles": "metadata-only",
            "unity_runtime_and_assembly_execution": "unsupported",
        },
        "support_level": "partial_metadata_and_reference_inspection",
        "limitations": [
            "Text YAML is inspected with bounded structural patterns; this is not a complete Unity YAML parser.",
            "GUID references are resolved only against .meta files discovered under Assets during this scan.",
            "Binary serialized objects and AssetBundles are listed but not decoded by this inspector.",
            "Only bounded samples of .meta, .unity, .prefab, and .asset text are inspected.",
        ],
    }
