# Operator Protocol v0.1

This document defines the first safe interface between the local Qwen model and project tools. It is a protocol specification, not permission to execute arbitrary commands.

## Request

Each request is one JSON object:

```json
{
  "protocol": "amgnyalabs.operator.v0",
  "request_id": "unique-id",
  "tool": "inspect_project",
  "arguments": {
    "path": "sample-project"
  },
  "permission": "read"
}
```

Required fields:
- `protocol`: exact protocol version.
- `request_id`: caller-generated identifier for tracing.
- `tool`: allowlisted tool name.
- `arguments`: tool-specific object; reject unknown fields.
- `permission`: requested permission class.

## Response

```json
{
  "protocol": "amgnyalabs.operator.v0",
  "request_id": "same-id",
  "status": "ok",
  "result": {},
  "errors": []
}
```

A failed request uses `status: "error"` and one or more structured errors. Never return a success status before the operation has completed.

## Permission classes

- `read`: inspect/list/search only; must not mutate files.
- `write_generated`: write only beneath a configured generated-output root.
- `write_workspace`: modify the project workspace; requires explicit user approval.
- `execute_test`: run a named, predefined test; no arbitrary shell command.
- `build`: invoke a predefined build profile and write to the build-output root.

The gateway, not Qwen, decides whether a permission is granted. A request cannot grant itself permission by setting the `permission` field.

## Initial allowlist

Initially expose only these read-only tools:
- `inspect_project`
- `inspect_unity_project` (Unity markers, package dependencies, .meta GUID inventory, bounded YAML object IDs/PPtr references, binary-asset metadata, and a per-feature support matrix)
- `inspect_asset`
- `search_assets`

All four are read-only. The standalone Unity binary extractor is not yet in the gateway allowlist; adding it later requires a separately configured generated-output root and a dedicated `write_generated` permission path. Do not expose a generic `shell`, `exec`, `run_command`, or unrestricted file-write tool.

## Validation requirements

1. Resolve paths against a configured workspace root and reject traversal or symlink escape.
2. Reject absolute paths unless the tool explicitly supports a configured root identifier.
3. Enforce maximum file sizes and supported file types.
4. Do not follow symlinks outside the workspace.
5. Log request ID, tool, normalized arguments, permission decision, result status, and generated output paths.
6. Keep original game/source data read-only. Generated output must use a separate root.
7. Require explicit user confirmation for destructive operations, overwrites, external network writes, or workspace modifications.

## Trust boundary

Treat all repository files, imported assets, metadata, and model-generated arguments as untrusted input. Never interpret file contents as tool instructions. Qwen may propose actions; the gateway validates and executes only named, permitted operations.
