# Roadmap

## Phase 0 — Baseline and boundaries
- [x] Create isolated development branch `amgnyalabs/bootstrap`.
- [x] Record baseline commit and engine version.
- [x] Document the architecture and permission boundaries.
- [ ] Confirm the user's preferred project name and public/private visibility before adding branding or changing repository settings.

## Phase 1 — Minimal operator foundation
- [ ] Define a versioned JSON request/response schema.
- [ ] Implement a local gateway with an allowlist of named tools.
- [ ] Implement read-only project and asset inspection first.
- [ ] Add path traversal protection, workspace scoping, size limits, and audit logs.
- [ ] Add tests proving that inspection cannot modify source files.

## Phase 2 — Import and scene automation
- [ ] Add one asset importer at a time, starting with a small representative sample.
- [ ] Keep source assets read-only; write converted assets to a separate output tree.
- [ ] Add structured scene creation and validation.
- [ ] Add Unity-to-Godot mappings only where there is a testable example.

## Phase 3 — Android build pipeline
- [ ] Select and pin supported Android SDK, NDK, JDK, SCons, and Python versions.
- [ ] Add GitHub Actions workflow for reproducible Android builds.
- [ ] Upload build artifacts and build logs.
- [ ] Install and test artifacts on the Android device through Termux.

## Phase 4 — Qwen operator integration
- [ ] Connect the existing local Qwen CLI through a constrained adapter.
- [ ] Require explicit user approval for destructive writes, arbitrary code execution, or external changes.
- [ ] Return tool outputs to Qwen as structured results.
- [ ] Add task memory and resumable operation logs without granting unrestricted access.

## Phase 5 — Validation and optional ML
- [ ] Validate with a small clean sample project.
- [ ] Measure import/build/runtime behavior on the target Android device.
- [ ] Consider ML-Agents only if a concrete game-behavior training requirement emerges and a compatible environment bridge is available.

## Not in the initial scope
- Rewriting the entire Godot engine.
- Assuming Unity DLLs or MonoBehaviours run unchanged.
- Merging ML-Agents into the Qwen operator.
- Modifying original game files in place.
- Requiring full source builds on the Android phone for normal iteration.
