#!/usr/bin/env python3
"""Constrained local Qwen CLI adapter for the read-only AmgNya gateway.

The model can request only the gateway's three read-only tools. Model output is
never interpreted as a shell command or executable code.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

GATEWAY_DIR = Path(__file__).resolve().parents[1] / "operator_gateway"
sys.path.insert(0, str(GATEWAY_DIR))
from gateway import PROTOCOL, ReadOnlyGateway

ALLOWED_TOOLS = {"inspect_project", "inspect_asset", "search_assets"}
MAX_TASK_CHARS = 4000
MAX_MODEL_OUTPUT_CHARS = 20000


class AdapterError(Exception):
    pass


def build_request_prompt(task: str, request_id: str) -> str:
    return (
        "You are a read-only project inspection planner. Choose exactly one tool "
        "from inspect_project, inspect_asset, search_assets. Never propose shell "
        "commands, code execution, writes, conversions, or network actions. "
        "Return exactly one JSON object and no markdown, using this schema: "
        '{"protocol":"amgnyalabs.operator.v0","request_id":"'
        + request_id
        + '","tool":"inspect_project","arguments":{"path":".","max_entries":100},"permission":"read"}. '
        "Use only arguments valid for the selected tool. inspect_project accepts "
        "path and max_entries; inspect_asset accepts only path; search_assets "
        "accepts query, path, extensions, limit. If the task cannot be fulfilled "
        "with these tools, return an inspect_project request for path '.'.\n"
        "User task:\n"
        + task
    )


def extract_json_object(output: str) -> dict[str, Any]:
    if not isinstance(output, str) or len(output) > MAX_MODEL_OUTPUT_CHARS:
        raise AdapterError("model output is empty or exceeds the output limit")
    # Scan balanced braces so CLI banners/log lines do not break JSON parsing.
    start = output.find("{")
    while start >= 0:
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(output)):
            char = output[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = output[start:index + 1]
                    try:
                        value = json.loads(candidate)
                    except json.JSONDecodeError:
                        break
                    if isinstance(value, dict):
                        return value
                    break
        start = output.find("{", start + 1)
    raise AdapterError("Qwen did not return a valid JSON object")


def validate_request(request: Any, request_id: str) -> dict[str, Any]:
    required = {"protocol", "request_id", "tool", "arguments", "permission"}
    if not isinstance(request, dict) or set(request) != required:
        raise AdapterError("model request has missing or unknown fields")
    if request["protocol"] != PROTOCOL or request["request_id"] != request_id:
        raise AdapterError("model request protocol or request_id mismatch")
    if request["tool"] not in ALLOWED_TOOLS:
        raise AdapterError("model requested a tool outside the read-only allowlist")
    if not isinstance(request["arguments"], dict) or request["permission"] != "read":
        raise AdapterError("model request must contain object arguments and read permission")
    return request


def run_qwen(
    llama_cli: str,
    model: str,
    prompt: str,
    *,
    context: int,
    threads: int,
    tokens: int,
    timeout: int,
) -> str:
    command = [
        llama_cli, "-m", model, "-c", str(context), "-t", str(threads),
        "-n", str(tokens), "--temp", "0", "-p", prompt,
    ]
    try:
        completed = subprocess.run(
            command, check=False, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdapterError("Qwen CLI timed out") from exc
    except OSError as exc:
        raise AdapterError(f"could not start Qwen CLI: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout)[-1500:]
        raise AdapterError(f"Qwen CLI exited with code {completed.returncode}: {detail}")
    if len(completed.stdout) > MAX_MODEL_OUTPUT_CHARS:
        raise AdapterError("Qwen CLI output exceeded the configured limit")
    return completed.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--llama-cli", default="llama-cli")
    parser.add_argument("--context", type=int, default=4096)
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--tokens", type=int, default=384)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("task", help="inspection task for Qwen")
    args = parser.parse_args()

    if not 1 <= len(args.task) <= MAX_TASK_CHARS:
        parser.error(f"task must contain 1 to {MAX_TASK_CHARS} characters")
    if args.context < 512 or args.threads < 1 or not 1 <= args.tokens <= 1024:
        parser.error("context/threads/tokens are outside safe limits")

    try:
        gateway = ReadOnlyGateway(Path(args.workspace))
        request_id = str(uuid.uuid4())
        prompt = build_request_prompt(args.task, request_id)
        model_output = run_qwen(
            args.llama_cli, args.model, prompt, context=args.context,
            threads=args.threads, tokens=args.tokens, timeout=args.timeout,
        )
        request = validate_request(extract_json_object(model_output), request_id)
        response = gateway.handle(request)
        print(json.dumps({
            "adapter_status": "ok",
            "tool_response": response,
        }, ensure_ascii=False))
        return 0 if response["status"] == "ok" else 1
    except (AdapterError, OSError, ValueError) as exc:
        print(json.dumps({
            "adapter_status": "error",
            "error": str(exc),
        }, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
