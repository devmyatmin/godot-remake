#!/usr/bin/env python3
"""PATH shim for GNU ar that chunks large object lists to avoid ARG_MAX."""
import os
import shutil
import subprocess
import sys

wrapper_dir = os.path.realpath(os.path.dirname(__file__))
search_path = os.pathsep.join(
    entry for entry in os.environ.get("PATH", "").split(os.pathsep)
    if os.path.realpath(entry or ".") != wrapper_dir
)
real_ar = shutil.which("ar", path=search_path)
if not real_ar:
    raise SystemExit("ar_chunker: could not locate the real system ar")

args = sys.argv[1:]
if len(args) < 3:
    os.execv(real_ar, [real_ar, *args])

# SCons invokes ar as: operation/flags, archive path, object files...
prefix = args[:2]
objects = args[2:]
limit = 48 * 1024
chunks = []
current = []
current_size = sum(len(arg.encode()) + 1 for arg in prefix)

for obj in objects:
    size = len(obj.encode()) + 1
    if current and current_size + size > limit:
        chunks.append(current)
        current = []
        current_size = sum(len(arg.encode()) + 1 for arg in prefix)
    current.append(obj)
    current_size += size

if current:
    chunks.append(current)

for chunk in chunks:
    subprocess.run([real_ar, *prefix, *chunk], check=True)
