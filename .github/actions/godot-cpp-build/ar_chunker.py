#!/usr/bin/env python3
"""Chunk GNU ar inputs to stay below the Linux exec argument-size limit.

SCons normally passes every generated godot-cpp object to one ar invocation.
Large editor APIs can exceed ARG_MAX. GNU ar can safely add objects to the
same archive in multiple invocations, so split only the object arguments.
"""
import os
import shutil
import subprocess
import sys

args = sys.argv[1:]
real_ar = shutil.which("ar")
if not real_ar:
    raise SystemExit("ar_chunker: could not locate the system 'ar' executable")

# GNU ar invocation from SCons: ARFLAGS, archive target, then object files.
if len(args) < 3:
    os.execv(real_ar, [real_ar, *args])

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
