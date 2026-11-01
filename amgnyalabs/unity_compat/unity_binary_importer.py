"""Best-effort, read-only Unity binary asset extraction into a separate generated root.

UnityPy is an optional runtime dependency. Each Unity object is handled independently:
one unsupported or malformed object must not discard other successfully exported objects.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {".assets", ".bundle", ".unity3d", ".resource", ".ress", ".ress"}
MAX_OBJECTS = 10000
MAX_OUTPUT_BYTES_PER_OBJECT = 256 * 1024 * 1024


def _safe_name(value: Any, fallback: str) -> str:
    text = str(value or fallback)
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._")
    return (text or fallback)[:100]


def _object_name(obj: Any) -> str:
    try:
        return str(obj.peek_name() or "unnamed")
    except Exception:
        return "unnamed"


def _write_bytes(path: Path, payload: Any) -> int:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    if not isinstance(payload, (bytes, bytearray, memoryview)):
        raise TypeError("exporter did not return bytes")
    size = len(payload)
    if size > MAX_OUTPUT_BYTES_PER_OBJECT:
        raise ValueError(f"object output exceeds {MAX_OUTPUT_BYTES_PER_OBJECT} bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)
    return size



def _json_safe(value: Any, depth: int = 0) -> Any:
    if depth > 64:
        return {"$truncated": "maximum nesting depth"}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (bytes, bytearray, memoryview)):
        return {"$encoding": "base64", "data": base64.b64encode(bytes(value)).decode("ascii")}
    if isinstance(value, dict):
        return {str(key): _json_safe(item, depth + 1) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item, depth + 1) for item in value]
    return {"$unsupported_type": type(value).__name__, "repr": repr(value)[:500]}

def _export_object(obj: Any, object_type: str, destination: Path) -> tuple[list[str], int, str]:
    parsed = obj.parse_as_object()
    name = _safe_name(getattr(parsed, "m_Name", None) or getattr(parsed, "name", None), "unnamed")
    base = f"{int(getattr(obj, 'path_id', 0))}_{name}"

    if object_type in {"Texture2D", "Sprite"}:
        image = getattr(parsed, "image", None)
        if image is None:
            raise ValueError("image decoder returned no image")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        path = destination / f"{base}.png"
        size = _write_bytes(path, buffer.getvalue())
        return [path.as_posix()], size, "exported_png"

    if object_type == "Mesh":
        exported = parsed.export()
        path = destination / f"{base}.obj"
        size = _write_bytes(path, exported)
        return [path.as_posix()], size, "exported_obj"

    if object_type == "AudioClip":
        samples = getattr(parsed, "samples", {}) or {}
        outputs: list[str] = []
        total = 0
        for sample_name, sample_data in samples.items():
            safe_sample = _safe_name(sample_name, "audio")
            path = destination / f"{base}_{safe_sample}.wav"
            total += _write_bytes(path, sample_data)
            outputs.append(path.as_posix())
        if not outputs:
            raise ValueError("AudioClip contains no decodable samples")
        return outputs, total, "exported_wav"

    if object_type == "Font":
        font_data = getattr(parsed, "m_FontData", b"")
        if not font_data:
            raise ValueError("Font contains no embedded font data")
        extension = ".otf" if bytes(font_data[:4]) == b"OTTO" else ".ttf"
        path = destination / f"{base}{extension}"
        size = _write_bytes(path, font_data)
        return [path.as_posix()], size, "exported_font"

    if object_type == "MonoBehaviour":
        tree = obj.parse_as_dict()
        payload = json.dumps(_json_safe(tree), ensure_ascii=False, indent=2)
        path = destination / f"{base}.json"
        size = _write_bytes(path, payload)
        return [path.as_posix()], size, "exported_typetree_json"

    if object_type == "TextAsset":
        text_data = getattr(parsed, "m_Script", None)
        if text_data is None:
            raise ValueError("TextAsset has no m_Script payload")
        path = destination / f"{base}.txt"
        if isinstance(text_data, str):
            text_data = text_data.encode("utf-8", "surrogateescape")
        size = _write_bytes(path, text_data)
        return [path.as_posix()], size, "exported_text"

    return [], 0, "metadata_only_unsupported_exporter"


def import_unity_file(source_file: Path, output_root: Path, max_objects: int = 3000) -> dict[str, Any]:
    """Extract supported objects from one Unity serialized file/bundle without modifying it."""
    requested_source = source_file.expanduser()
    if requested_source.is_symlink():
        raise ValueError("source must not be a symlink")
    source = requested_source.resolve(strict=True)
    if not source.is_file():
        raise ValueError("source must be an existing regular file")
    if not isinstance(max_objects, int) or isinstance(max_objects, bool) or not 1 <= max_objects <= MAX_OBJECTS:
        raise ValueError(f"max_objects must be between 1 and {MAX_OBJECTS}")

    requested_output = output_root.expanduser()
    if requested_output.is_symlink():
        raise ValueError("generated output root cannot be a symlink")
    output = requested_output.resolve()
    if output == source.parent or source.parent in output.parents:
        raise ValueError("generated output must be outside the original source directory")
    if output == source or output in source.parents:
        raise ValueError("generated output cannot contain or replace the source")
    output.mkdir(parents=True, exist_ok=True)

    try:
        import UnityPy  # type: ignore
    except ImportError as exc:
        raise RuntimeError("UnityPy is required; install the pinned importer requirements") from exc

    env = UnityPy.load(str(source))
    results: list[dict[str, Any]] = []
    objects_seen = 0
    exported_objects = 0
    metadata_only_objects = 0
    failed_objects = 0
    total_bytes = 0
    truncated = False
    source_output = output / _safe_name(source.name, "unity_source")
    if source_output.is_symlink():
        raise ValueError("per-source output directory cannot be a symlink")
    source_output.mkdir(parents=True, exist_ok=True)

    for obj in env.objects:
        objects_seen += 1
        if objects_seen > max_objects:
            truncated = True
            break
        object_type = str(getattr(getattr(obj, "type", None), "name", "Unknown"))
        object_id = int(getattr(obj, "path_id", 0))
        object_name = _object_name(obj)
        record: dict[str, Any] = {
            "path_id": object_id,
            "type": object_type,
            "name": object_name,
            "status": "pending",
            "outputs": [],
            "bytes_written": 0,
            "error": None,
        }
        try:
            files, size, status = _export_object(obj, object_type, source_output)
            record.update({"status": status, "outputs": files, "bytes_written": size})
            total_bytes += size
            if files:
                exported_objects += 1
            else:
                metadata_only_objects += 1
        except Exception as exc:
            record.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}"})
            failed_objects += 1
        results.append(record)

    report = {
        "source_file": source.as_posix(),
        "source_modified": False,
        "output_root": output.as_posix(),
        "objects_seen": min(objects_seen, max_objects),
        "truncated": truncated,
        "exported_objects": exported_objects,
        "metadata_only_objects": metadata_only_objects,
        "failed_objects": failed_objects,
        "bytes_written": total_bytes,
        "object_results": results,
        "limitations": [
            "This is a best-effort extractor, not a Unity runtime or complete project importer.",
            "Materials, shaders, scene/prefab reconstruction, MonoBehaviours, and unknown object types are not converted yet.",
            "A successful extraction does not prove the result is behaviorally equivalent in Godot.",
            "The source file and sidecars are opened only through UnityPy; all exports are written under the separate generated root.",
        ],
    }
    report_path = source_output / "import_report.json"
    with report_path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="one Unity .assets or AssetBundle file")
    parser.add_argument("--output", required=True, type=Path, help="separate generated-output root")
    parser.add_argument("--max-objects", type=int, default=3000)
    args = parser.parse_args(argv)
    try:
        report = import_unity_file(args.source, args.output, args.max_objects)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "partial" if report["failed_objects"] or report["metadata_only_objects"] or report["truncated"] else "ok",
        "objects_seen": report["objects_seen"],
        "exported_objects": report["exported_objects"],
        "metadata_only_objects": report["metadata_only_objects"],
        "failed_objects": report["failed_objects"],
        "output_root": report["output_root"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
