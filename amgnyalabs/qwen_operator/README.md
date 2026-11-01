# Local Qwen Operator Adapter

This adapter connects a local `llama-cli` process to the read-only gateway. It does not start a model server and does not execute commands proposed by Qwen.

## Requirements

- Python 3.10+
- `llama-cli` available on PATH (or pass `--llama-cli`)
- A local GGUF model
- The gateway and adapter files in this repository

## Run

From the repository root:

```sh
python amgnyalabs/qwen_operator/qwen_adapter.py \
  --workspace /absolute/path/to/project \
  --model "$HOME/storage/shared/Download/aimodel/Qwen2.5-Coder-7B-Instruct-abliterated-Q4_K_M.gguf" \
  "List the Unity project structure and identify its Packages and ProjectSettings folders."
```

Optional tuning flags: `--context 4096 --threads 6 --tokens 384 --timeout 180`.

## Safety boundary

1. Qwen is prompted to return one JSON request for a named read-only tool.
2. The adapter parses and validates the JSON, protocol, request ID, tool allowlist, and read permission.
3. The adapter passes the request to the gateway in-process.
4. The gateway independently validates paths and arguments.
5. The adapter prints the structured gateway response.

Qwen output is never passed to a shell, Python evaluator, or arbitrary process. The only subprocess launched is the fixed `llama-cli` executable with an argument list (no shell). The current gateway exposes only `inspect_project`, `inspect_asset`, and `search_assets`; it does not read file contents or modify files.

This is a first integration step, not a full autonomous agent. It currently performs one tool request per run and returns structured results; multi-step planning, content-aware Unity parsers, conversion, and approved write/build tools are later milestones. Keep the workspace limited to files Qwen is allowed to inspect.

## Tests

```sh
python -m unittest discover -s amgnyalabs/qwen_operator/tests -v
```
