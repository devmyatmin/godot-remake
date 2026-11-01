# Read-only Operator Gateway

A minimal Python standard-library gateway for local Qwen integration. It accepts one JSON request per input line and emits one JSON response per line.

## Requirements

- Python 3.10+
- No third-party packages

## Run locally

From the repository root:

\`\`\`sh
python amgnyalabs/operator_gateway/gateway.py --workspace /absolute/path/to/project
\`\`\`

Then send a request on stdin:

\`\`\`json
{"protocol":"amgnyalabs.operator.v0","request_id":"demo-001","tool":"inspect_project","arguments":{"path":".","max_entries":100},"permission":"read"}
\`\`\`

The gateway currently supports only:
- \`inspect_project\`: bounded directory inventory and extension counts.
- \`inspect_asset\`: file metadata (does not read file contents).
- \`search_assets\`: bounded filename search with optional extension filters.

## Security behavior

- Read-only allowlist; no shell, arbitrary execution, or write tools.
- All paths are relative to the configured workspace.
- Absolute paths, parent traversal, and symlinks are rejected.
- Results are bounded; inventory and search have hard limits.
- File contents are not returned.
- Unknown request fields and tools are rejected.

This is an initial local prototype, not a complete sandbox. Run it under an OS account/container with access limited to the intended workspace. Do not expose it directly to an untrusted network client.

## Tests

From this directory:

\`\`\`sh
python -m unittest discover -s tests -v
\`\`\`

The gateway is intentionally metadata-only. Real Unity/Godot asset parsing and conversion will be separate tools added only after the read-only boundary is validated.
