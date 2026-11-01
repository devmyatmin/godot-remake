#!/usr/bin/env python3
"""Read-only JSON tool gateway for the AmgNya Engine Layer (protocol v0)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from unity_compat.project_inspector import inspect_unity_project

PROTOCOL = "amgnyalabs.operator.v0"
MAX_ENTRIES = 5000
MAX_SEARCH_RESULTS = 500
MAX_EXTENSIONS = 32


class GatewayError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _string(value: Any, field: str, *, default: str | None = None) -> str:
    if value is None and default is not None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise GatewayError("invalid_argument", f"{field} must be a non-empty string")
    return value


class ReadOnlyGateway:
    """Expose only bounded, read-only inspection tools under one workspace."""

    def __init__(self, workspace: str | Path) -> None:
        self.root = Path(workspace).expanduser().resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("workspace root must be an existing directory")

    def _resolve(self, relative: Any, *, must_exist: bool = True) -> Path:
        raw = _string(relative, "path", default=".")
        # Treat paths as portable workspace-relative paths, not host paths.
        if "\\" in raw or "\x00" in raw:
            raise GatewayError("invalid_path", "path contains a forbidden character")
        rel = PurePosixPath(raw)
        if rel.is_absolute() or any(part in ("..", "") for part in rel.parts):
            if raw != ".":
                raise GatewayError("path_outside_workspace", "absolute paths and '..' are not allowed")

        candidate = self.root
        for part in (() if raw == "." else rel.parts):
            candidate = candidate / part
            if candidate.is_symlink():
                raise GatewayError("symlink_denied", "symbolic links are not followed")
        try:
            resolved = candidate.resolve(strict=must_exist)
        except FileNotFoundError:
            raise GatewayError("not_found", f"path does not exist: {raw}") from None
        except OSError as exc:
            raise GatewayError("path_error", str(exc)) from None

        if resolved != self.root and self.root not in resolved.parents:
            raise GatewayError("path_outside_workspace", "resolved path escapes workspace")
        if must_exist and not resolved.exists():
            raise GatewayError("not_found", f"path does not exist: {raw}")
        return resolved

    @staticmethod
    def _metadata(path: Path, root: Path) -> dict[str, Any]:
        stat = path.stat(follow_symlinks=False)
        return {
            "path": path.relative_to(root).as_posix() or ".",
            "name": path.name or ".",
            "kind": "directory" if path.is_dir() else "file",
            "extension": path.suffix.lower(),
            "size_bytes": stat.st_size if path.is_file() else None,
            "modified_utc": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat(),
        }

    def inspect_project(self, args: dict[str, Any]) -> dict[str, Any]:
        allowed = {"path", "max_entries"}
        if set(args) - allowed:
            raise GatewayError("unknown_argument", "inspect_project received unknown arguments")
        start = self._resolve(args.get("path", "."))
        if not start.is_dir():
            raise GatewayError("not_a_directory", "path must identify a directory")
        limit = args.get("max_entries", 1000)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_ENTRIES:
            raise GatewayError("invalid_argument", f"max_entries must be between 1 and {MAX_ENTRIES}")

        stack = [start]
        entries: list[dict[str, Any]] = []
        extension_counts: dict[str, int] = {}
        skipped_symlinks = 0
        truncated = False

        while stack:
            directory = stack.pop()
            try:
                children = sorted(os.scandir(directory), key=lambda item: item.name.casefold())
            except OSError as exc:
                raise GatewayError("scan_error", f"cannot scan {directory.relative_to(self.root)}: {exc}") from None
            subdirs: list[Path] = []
            for child in children:
                if child.is_symlink():
                    skipped_symlinks += 1
                    continue
                child_path = Path(child.path)
                try:
                    info = self._metadata(child_path, self.root)
                except OSError:
                    continue
                if len(entries) >= limit:
                    truncated = True
                    break
                entries.append(info)
                if info["kind"] == "directory":
                    subdirs.append(child_path)
                else:
                    ext = info["extension"] or "[no extension]"
                    extension_counts[ext] = extension_counts.get(ext, 0) + 1
            if truncated:
                break
            stack.extend(reversed(subdirs))

        return {
            "root": ".",
            "inspected_path": start.relative_to(self.root).as_posix() or ".",
            "entry_count": len(entries),
            "truncated": truncated,
            "skipped_symlinks": skipped_symlinks,
            "extension_counts": dict(sorted(extension_counts.items())),
            "entries": entries,
        }

    def inspect_unity_project(self, args: dict[str, Any]) -> dict[str, Any]:
        allowed = {"path", "max_files"}
        if set(args) - allowed:
            raise GatewayError("unknown_argument", "inspect_unity_project received unknown arguments")
        start = self._resolve(args.get("path", "."))
        if not start.is_dir():
            raise GatewayError("not_a_directory", "Unity project path must identify a directory")
        limit = args.get("max_files", 3000)
        try:
            return inspect_unity_project(start, limit)
        except ValueError as exc:
            raise GatewayError("invalid_argument", str(exc)) from None
        except OSError:
            raise GatewayError("inspection_error", "Unity project inspection failed") from None

    def inspect_asset(self, args: dict[str, Any]) -> dict[str, Any]:
        if set(args) != {"path"}:
            raise GatewayError("invalid_argument", "inspect_asset requires only 'path'")
        target = self._resolve(args["path"])
        if not target.is_file():
            raise GatewayError("not_a_file", "path must identify a regular file")
        return self._metadata(target, self.root)

    def search_assets(self, args: dict[str, Any]) -> dict[str, Any]:
        allowed = {"query", "path", "extensions", "limit"}
        if set(args) - allowed:
            raise GatewayError("unknown_argument", "search_assets received unknown arguments")
        query = _string(args.get("query"), "query").casefold()
        start = self._resolve(args.get("path", "."))
        if not start.is_dir():
            raise GatewayError("not_a_directory", "search path must identify a directory")

        raw_extensions = args.get("extensions", [])
        if not isinstance(raw_extensions, list) or len(raw_extensions) > MAX_EXTENSIONS:
            raise GatewayError("invalid_argument", "extensions must be a short list of suffixes")
        extensions: set[str] = set()
        for ext in raw_extensions:
            if not isinstance(ext, str) or not ext.startswith(".") or "/" in ext or "\\" in ext:
                raise GatewayError("invalid_argument", "each extension must look like '.png'")
            extensions.add(ext.casefold())

        limit = args.get("limit", 100)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_SEARCH_RESULTS:
            raise GatewayError("invalid_argument", f"limit must be between 1 and {MAX_SEARCH_RESULTS}")

        stack = [start]
        matches: list[dict[str, Any]] = []
        scanned = 0
        truncated = False
        while stack:
            directory = stack.pop()
            try:
                children = sorted(os.scandir(directory), key=lambda item: item.name.casefold())
            except OSError:
                continue
            subdirs: list[Path] = []
            for child in children:
                if child.is_symlink():
                    continue
                item = Path(child.path)
                try:
                    if child.is_dir(follow_symlinks=False):
                        subdirs.append(item)
                        continue
                    if not child.is_file(follow_symlinks=False):
                        continue
                    scanned += 1
                    suffix = item.suffix.casefold()
                    if query in item.name.casefold() and (not extensions or suffix in extensions):
                        if len(matches) >= limit:
                            truncated = True
                            break
                        matches.append(self._metadata(item, self.root))
                except OSError:
                    continue
            if truncated:
                break
            stack.extend(reversed(subdirs))

        return {
            "query": query,
            "scanned_files": scanned,
            "match_count": len(matches),
            "truncated": truncated,
            "matches": matches,
        }

    def handle(self, request: Any) -> dict[str, Any]:
        request_id = None
        try:
            if not isinstance(request, dict):
                raise GatewayError("invalid_request", "request must be a JSON object")
            request_id = request.get("request_id")
            if request.get("protocol") != PROTOCOL:
                raise GatewayError("protocol_mismatch", f"protocol must be {PROTOCOL}")
            if not isinstance(request_id, str) or not request_id.strip():
                raise GatewayError("invalid_request", "request_id must be a non-empty string")
            if set(request) != {"protocol", "request_id", "tool", "arguments", "permission"}:
                raise GatewayError("invalid_request", "request has missing or unknown fields")
            if request.get("permission") != "read":
                raise GatewayError("permission_denied", "this gateway version permits read-only requests")
            tool = request.get("tool")
            args = request.get("arguments")
            if not isinstance(args, dict):
                raise GatewayError("invalid_argument", "arguments must be an object")
            tools = {
                "inspect_project": self.inspect_project,
                "inspect_unity_project": self.inspect_unity_project,
                "inspect_asset": self.inspect_asset,
                "search_assets": self.search_assets,
            }
            if tool not in tools:
                raise GatewayError("unknown_tool", "tool is not in the read-only allowlist")
            result = tools[tool](args)
            return {
                "protocol": PROTOCOL,
                "request_id": request_id,
                "status": "ok",
                "result": result,
                "errors": [],
            }
        except GatewayError as exc:
            return {
                "protocol": PROTOCOL,
                "request_id": request_id,
                "status": "error",
                "result": None,
                "errors": [{"code": exc.code, "message": exc.message}],
            }
        except Exception:
            # Avoid leaking host paths or stack traces to the model-facing client.
            return {
                "protocol": PROTOCOL,
                "request_id": request_id,
                "status": "error",
                "result": None,
                "errors": [{"code": "internal_error", "message": "request failed"}],
            }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="existing workspace root")
    options = parser.parse_args()
    try:
        gateway = ReadOnlyGateway(options.workspace)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "fatal", "error": str(exc)}), file=sys.stderr)
        return 2

    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = {
                "protocol": PROTOCOL,
                "request_id": None,
                "status": "error",
                "result": None,
                "errors": [{"code": "invalid_json", "message": "input line is not valid JSON"}],
            }
        else:
            response = gateway.handle(request)
        print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
